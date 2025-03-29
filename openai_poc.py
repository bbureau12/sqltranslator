from openai import OpenAI
client = OpenAI()

schemas = """
CREATE TABLE Users (
    user_id INTEGER NOT NULL,
    first_name TEXT NOT NULL,
    email_address TEXT NOT NULL,
    last_name TEXT NOT NULL,
    street_address TEXT NOT NULL,
    city TEXT NOT NULL,
    state_province TEXT NOT NULL,
    postal_code TEXT NOT NULL,
    PRIMARY KEY(user_id)
);

CREATE TABLE Items (
    item_id INTEGER NOT NULL,
    item_name TEXT NOT NULL,
    item_price REAL NOT NULL,
    PRIMARY KEY(item_id)
);

CREATE TABLE Orders (
    order_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    order_amount REAL NOT NULL,
    PRIMARY KEY(order_id),
    FOREIGN KEY(user_id) REFERENCES Users(user_id),
    FOREIGN KEY(item_id) REFERENCES Items(item_id)
);
"""

def translate_to_sql(phrase):
    prompt = f"""
Given the following table schemas:
{schemas}

Translate the following natural language query to SQL: {phrase}
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
    
phrase = "Show me all customers who live in Seattle"
sql_query = translate_to_sql(phrase)
print(sql_query)