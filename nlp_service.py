import re
from fuzzywuzzy import fuzz
import inflect
import spacy

class Nlp_Service:
    def __init__(self, settingRepository, synonymRepository):
        self.settingRepository = settingRepository
        self.synonymRepository = synonymRepository
        # Loading our spacy model
        self.nlp = spacy.load("en_core_web_sm")
        self.inflect_engine = inflect.engine()
        self.sql_pertinent_words = {"like"}

    # An attempt to convert a human request to SQL via spaCy.  Will only work if you have valid table/column synonyms in the DB.
    def convert_to_sql(self, phrase):
        doc = self.nlp(phrase)
        tables = self.extract_table_name(doc)
        columns = []
        operators = []
        targets = []
        sql_commands = []
        if tables and len(tables) > 0:
            for subject in tables:
                columns.append(self.extract_column_name(doc, subject))
        else:
            raise Exception("Could not parse a table")
        if columns and len(columns) > 0:
            for column in columns:
                if column is None:
                    continue
                operators.append(self.extract_operator(doc, column))
                targets.append(self.extract_targets(doc))
        else:
            raise Exception("Could not parse column")
        if len(operators) > 0 and len(targets)>0:
            for i in range(len(tables)):
                table, tab_trigger, tab_trigger_index = tables[i]
                #Note for revision: collapse column and operator processing to one array
                column, col_trigger, col_trigger_index = columns[i][0] if i < len(columns) else None
                operator, op_tag = operators[0] if i < len(operators) else 'is'
                target = targets[i] if i < len(targets) else None
                # we have an invalid request here
                if column is None or target is None:
                        continue
                
                conjugated_target = self._conjugate_target(target, op_tag)

                sql_commands.append(f'SELECT * FROM {table} WHERE {column} {self._convert_operator(operator)} {self._format_target(operator, conjugated_target)}')
        else: 
            raise Exception("Could not parse operator or target value")
        if len(sql_commands)>0:
            return sql_commands
        return []

    def extract_table_name(self, doc):
        subjects = []
        table_synonyms = self.synonymRepository.getAllTableSynonyms()
        if table_synonyms is None or len(table_synonyms) == 0:
            print("could not load table synonyms.")
            return
        # Iterate over tokens to find subjects of interest
        for token in doc:
            if token.text == "is":
                    t = True
            # A list of probable grammar structures our table could be 
            if token.dep_ in {"nsubj", "nsubjpass", "dobj", "pobj", "ROOT"} and token.pos_ in {"NOUN", "PRON"}:
                found_table = self._find_synonym_by_token(token, table_synonyms)
                if found_table == None:
                    continue
                # Generally, the first table would be the one we're going to search (Example: in I want all Users whose Address is X, I want Users)
                if len(subjects) > 0:
                    is_dependent = self._is_target_in_head_structure(token,  [subject[1] for subject in subjects])
                    if is_dependent:
                        continue                
                compound = " ".join([child.text for child in token.children if child.dep_ == "compound"])
                subject = f"{compound} {token.text}".strip()
                # Exclude subjects that are part of a larger noun phrase containing attributes like "name" or "surname"
                if not any(attr.dep_ in {"attr", "acomp"} for attr in token.head.children):
                    subjects.append((found_table["table_name"], subject, token.i))
        
        return subjects

    def extract_operator(self, doc, column_tuple):
        table_name, token_text, token_i = column_tuple[0]
        token = self._find_token_by_index(doc, token_i)
        if token is None:
            return ""
        # Example: all users whose name is John Johnson
        if token.head.lemma_== "be":
            return self._find_operator_qualifiers(token.head)
        for child in token.children:
            if child.lemma_== "be":
                return self._find_operator_qualifiers(child)
        #if the operator is past participle or verb participle (example: all people named John, all people who live in Seattle), "LIKE" is the safest bet.  If we only have one word, we can assume that we are probably only looking for part of an address or name (examples: John, Seattle, Minnesota etc):
        if token.tag_ in {"VBN", "VBP"}:
            return ("LIKE", token.tag_)

    def extract_column_name(self, doc, table_tuple):
        table_name, token_text, token_i = table_tuple
        token = self._find_token_by_index(doc, token_i)
        results = []
        if token is None:
            return ""
        
        column_parts = set()
        token_ids = []
        self._collect_column_parts(token, column_parts, token_ids)

        candidate = ' '.join(sorted(column_parts, key=lambda x: token.text.find(x)))
        if not candidate:
            return
        column_synonyms =  self.synonymRepository.getAllColumnSynonyms(table_name)
        found_column = self._find_synonym_by_text(candidate, column_synonyms)
        if found_column:
            #This will contain the column name (or join), the token text that located it, and the id of the originating token
            results.append((found_column, candidate, token_ids[0]))
        return results

    def extract_targets(self, doc):
        targets = []
        token_ids = []
        for token in doc:
            # Skip previously parsed tokens
            if token.i in token_ids:
                continue
            if token.dep_ in {'attr', 'oprd', 'dobj', 'pobj', 'nsubj', 'npadvmod'} and token.ent_type_ in {'PERSON', 'GPE'}:
                targets.append(self._collect_multiword_value_token(token, token_ids))
            elif token.dep_ == 'attr' and token.head.lemma_ == 'be':
                subject = [w for w in token.head.lefts if w.dep_ in {'nsubj', 'nsubjpass'}]
                if subject and subject[0].text in {'name', 'surname', 'address'}:
                    targets.append(self._collect_multiword_value_token(token, token_ids))
        return ' '.join(targets)

    def _find_operator_qualifiers(self, token):
        if token.head:
            if token.head.text in  self.sql_pertinent_words:
                return (token.head.text, token.pos_)
        if token.children:
            for child in token.children:
                if child.text in  self.sql_pertinent_words:
                    return (child.text, child.pos_)
        return (token, token.pos_)

    def _collect_column_parts(self, token, collected_parts, token_ids, process_head = True):
        if process_head:
            self._process_column_token(token.head, collected_parts, token_ids)
        for child in token.children:
            if child.dep_ in {'amod', 'compound', 'det', 'prep', 'acl', 'nmod', 'nsubj', 'poss', 'relcl'}:
                self._process_column_token(child, collected_parts, token_ids)
            else : 
                self._collect_column_parts(child, collected_parts, token_ids, False)

    # Examples: first name, street address
    def _collect_multiword_column_token(self, token, token_ids):
        result = []
        if token.lemma_ not in ('be') and token.pos_ not in ('PRON') and not token.dep_ in ('det', 'poss', 'prep'):
            token_ids.append(token.i)
            result.append(token.text)
        for child in token.children:
            if child.dep_ in ('amod', 'nmod', 'compound') and child.lemma_ not in ('be') and child.pos_ not in ('PRON') and not child.dep_ in ('det', 'poss', 'prep'):
                token_ids.append(token.i)
                result.append(child.text)
        if len(result) > 0:
            #need to reverse here as we are climbing down the tree
            result.reverse()
            return ' '.join(result)
        return None

    def _collect_multiword_value_token(self, token, token_ids):
        result = []
        if token.text == "Seattle":
            t = True
        if token.lemma_ not in ('be') and token.pos_ not in ('PRON') and not token.dep_ in ('det', 'poss', 'prep'):
            token_ids.append(token.i)
            result.append((token.text, token.i))
        for child in token.children:
            if child.dep_ in ('amod', 'nmod', 'compound', 'punct', 'npadvmod') and child.lemma_ not in ('be') and child.pos_ not in ('PRON') and not child.dep_ in ('det', 'poss', 'prep'):
                token_ids.append(child.i)
                result.append((child.text, child.i))
        if len(result) > 0:
            result_sorted = sorted(result, key=lambda x: x[1])
            # Extract only the text part in order
            result_text = [text for text, _ in result_sorted]
            return ' '.join(result_text)
        return None
    
    def _conjugate_target(self, target_value, operator_tag):
        # if we have a single-word target and a VBN or VBP operator (example: named, lived, where we don't know if first or last name)
        word_count = len(target_value.split(" "))
        if operator_tag in {"VBN", "VBP"} and word_count == 1:
            #assume this would be just portion of name, st address etc and add space (example usage: if someone says "I want people named John" they mean John Jones and John Doe, not Steve Johnson)
            return f'{target_value} '
        return target_value

    
    def _format_target(self, operator, target):
        if operator == 'LIKE':
            return f"'%{target}%'"
        return f"'{target}'"

    def _convert_operator(self, operator):
        if 'like' in operator.lower():
            return 'LIKE'
        return '='
    
    def _find_token_by_index(self, doc, index):
        if 0 <= index < len(doc):
            return doc[index]
        else:
            return None 
        
    def _find_synonym_by_text(self, text, table_synonyms):
        result = []
        if not text or len(text.replace(' ', ''))==0:
            return ''
        sanitized_input = self._sanitize_input(text).lower()
        if text=="first name":
            t = True
        #Note: we are checking both the original text, as well as the plural and singular versions.
        for entry in table_synonyms:
            if self._sanitize_input(entry["synonym"]).lower() in sanitized_input:
                # in cases like first name, last name, name, surname etc we want the closest match
                similarity = fuzz.ratio(entry["synonym"].lower(), sanitized_input)
                result.append((entry["column_name"], similarity))
        if len(result) > 0:
            result.sort(key=lambda x: x[1], reverse=True)
            # Return the column name with the highest similarity
            return result[0][0]

        return None

    def _find_synonym_by_token(self, token, table_synonyms):
        #Note: we are checking both the original text, as well as the plural and singular versions.
        for input in [token.text, token.lemma_,  self.inflect_engine.plural(token.text)]:
            sanitized_input = self._sanitize_input(input).lower()
            for entry in table_synonyms:
                if entry["synonym"].lower() in sanitized_input:
                    return entry
        return None
        
    def _is_target_in_head_structure(self, token, targets):
        while token.head != token:
            if token.head.text in targets:
                return True
            token = token.head
        return False

    def _process_column_token(self, token, collected_parts, token_ids):
            if token.dep_ in {'amod', 'compound', 'det', 'prep', 'acl', 'nmod', 'nsubj', 'poss', 'relcl', 'ccomp'}:
                # we want to loop over these children (examples: users whose address, people who live in Seattle,) but not capture them.
                if token.lemma_ not in ('be') and token.pos_ not in ('PRON') and not token.dep_ in ('det', 'poss', 'prep'):
                    token_ids.append(token.i)
                    collected_parts.add(token.text)
                # For prepositions, include their objects
                if token.dep_ in ('prep', 'relcl'):
                    for child in token.children:
                        if child.dep_ in {'pobj', 'nmod', 'nsubj'}:
                            local_result = self._collect_multiword_column_token(child, token_ids)
                            if local_result and len(local_result) > 0:
                                collected_parts.add(self._collect_multiword_column_token(child, token_ids))
    def _sanitize_input(self, input):
        # Use regex to replace any digit or punctuation character with an empty string
        sanitized = re.sub(r'[0-9\W_]', '', input)
        # Remove any extra spaces that may have resulted from the replacements
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        return sanitized
