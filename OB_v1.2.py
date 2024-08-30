import pandas as pd
import re
from flask import Flask, request, render_template_string, redirect, url_for
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name('cedar-gift-432307-k2-e107b6f6c67e.json', scope)
gc = gspread.authorize(credentials)

# Load the latest dataset
latest_file_path = gc.open_by_key("1iGrx-5RSjDnqUSNlgiwxrjLSXeorjHkIhhlL9q2nSqA").worksheet("WorksheetName")  
data_latest = latest_file_path.get_all_values()

# Convert the data into a DataFrame
df_latest = pd.DataFrame(data_latest[1:], columns=data_latest[0]) 

# Load the old dataset
old_file_path = gc.open_by_key("12RDXlHCzw4a6lvcnZjJUZlKlf1lAqf8M-eqEkSmTi5k").worksheet("WorksheetName")
data_old = old_file_path.get_all_values()

# Convert the old data into a DataFrame
df_old = pd.DataFrame(data_old[1:], columns=data_old[0])

# Load the current datasets
#latest_file_path = 'OB/FTDH-CURRENT.xlsx'
#old_file_path = 'OB/FTDH JAN-JUL.xlsx'

#def load_dataset(file_path):
#    return pd.read_excel(file_path)

def filter_and_process_data(df):
    required_columns = ['Sender', 'Statuses', 'BenificiaryAccountNumber']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' is missing from the dataset.")
    
    # Filter data based on specific criteria
    df['Sender'] = df['Sender'].str.strip()
    df = df[df['Sender'] != 'SADAPAY']
    df = df[df['Statuses'] != 'Invalid']
    return df

# Filter both datasets
df_latest_filtered = filter_and_process_data(df_latest)
df_old_filtered = filter_and_process_data(df_old)


# def filter_and_process_data(df):
#     required_columns = ['Sender', 'Statuses', 'BenificiaryAccountNumber']
#     for col in required_columns:
#         if col not in df.columns:
#             raise ValueError(f"Column '{col}' is missing from the dataset.")
    
#     df = df[df['Sender'] != 'SADAPAY']
#     df = df[df['Statuses'] != 'Invalid']
#     return df

# # Load both datasets
# df_latest = load_dataset(latest_file_path)
# df_old = load_dataset(old_file_path)

# # Filter the datasets
# df_latest = filter_and_process_data(df_latest)
# df_old = filter_and_process_data(df_old)

# Normalize time function
def normalize_time(time_str):
    time_str = re.sub(r'\D', '', time_str)
    if len(time_str) == 6:
        hours = time_str[:2]
        minutes = time_str[2:4]
    elif len(time_str) == 4:
        hours = time_str[:2]
        minutes = time_str[2:4]
    else:
        hours = '00'
        minutes = '00'
    return f"{hours.zfill(2)}:{minutes.zfill(2)}"

# Extract account number function
def extract_account_number(account_number):
    return account_number[-10:]

# Generate message function
def generate_message(df, account_number):
    print(f"Searching for account number: {account_number}")
    account_number = extract_account_number(str(account_number))

    df['ExtractedAccountNumber'] = df['BenificiaryAccountNumber'].apply(lambda x: extract_account_number(str(x)))
    user_data = df[df['ExtractedAccountNumber'] == account_number]

    if user_data.empty:
        return "No data found for the given account number."

    grouped = user_data.groupby('Sender')
    messages = []

    for bank, transactions in grouped:
        transaction_details = ""
        for index, row in transactions.iterrows():
            amount = row['TrxAmount']
            trx_date = pd.to_datetime(row['TrxDate']).strftime('%Y-%m-%d')
            trx_time = normalize_time(str(row['Time']))
            transaction_details += f"PKR {amount}/- received on {trx_date} at {trx_time}<br>"

        message = f"""Hey! :wave:<br>
        We received complaints from {bank} for the disputed transactions as following:<br>
        {transaction_details.strip()}<br>
        In accordance with industry-wide practice, we have deactivated your account until further notice. In the meanwhile, it would be really helpful if you could please provide us the following details written on a paper:<br>
        * Reason of transaction<br>
        * Relationship with sender (if any)<br>
        * Any proof the user can provide that the transaction was genuine<br>
        * A picture of your CNIC (both front and back)<br>
        Also, we recommend reaching out to {bank} and asking them to unblock your account directly. Once they do and send us an email clearing your account, all Sadapay services will be restored.
        Thank you! :pray:"""

        messages.append(message)

    return "<br><br>".join(messages)

# HTML Template
home_page = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OB Generator</title>
    <div class="bottom-container">
    <h5 style="position: fixed; bottom: 10px; width: 100%; text-align: center; font-size: 0.75rem; color: #666;">Designed by RAWN for Compliance</h5>
    <a href="https://www.buymeacoffee.com/rahmanawan99" target="_blank" class="support-button">Like this Project? Support me</a>
    </div>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-color: #f0f0f0;
        }
        .container {
            text-align: center;
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        input[type="text"] {
            padding: 0.5rem;
            width: 200px;
            margin-right: 1rem;
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        input[type="submit"], button {
            padding: 0.5rem 1rem;
            background-color: #28a745;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin-right: 0.5rem;
        }
        input[type="submit"]:hover, button:hover {
            background-color: #218838;
        }
        .result {
            margin-top: 1rem;
            font-size: 1.2rem;
        }
        .error {
            color: red;
        }
        .logo {
            max-width: 150px;
            margin-bottom: 20px;
        }
        .support-button {
            background-color: #FFDD00;
            color: black;
            padding: 8px 15px;
            font-size: 16px;
            border: none;
            cursor: pointer;
            border-radius: 20px;
            text-decoration: none;
            box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.2); /* Optional: subtle shadow */

        }

        .support-button:hover {
            background-color: #FFCC00;
        }

        .bottom-container {
            position: fixed;
            bottom: 10px;
            width: 100%;
            text-align: center;
            font-size: 0.75rem;
            color: #666;
        }
        body {
            padding-bottom: 50px;
        }
    </style>
</head>
<body>
    <div class="container">
        <img src="static/SadaPay-Logo-Vector.svg-.png" alt="Logo" class="logo">
        <h1>OB Generator</h1>
        <form action="/" method="post">
            <input type="text" name="account_number" placeholder="Enter account number" required>
            <select name="database" required>
                <option value="latest">Latest Database (Excel Import Data)</option>
                <option value="old">Old Database (FTDH JAN-JUL)</option>
            </select>
            <input type="submit" value="Lookup">
        </form>
        <br>
        <a href="/internal">
            <input type="button" value="Go to Internal Lookup" style="padding: 0.5rem 1rem; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;">
        </a>
        {% if result is not none %}
            <div class="result" id="message">{{ result|safe }}</div>
            <button onclick="copyMessage()">Copy Message</button>
        {% endif %}
        {% if error is not none %}
            <div class="error">{{ error }}</div>
        {% endif %}
    </div>
    <script>
    function copyMessage() {
        const tempElement = document.createElement("textarea");
        tempElement.style.position = "fixed";
        tempElement.style.opacity = "0";
        tempElement.value = document.getElementById('message').innerText;

        document.body.appendChild(tempElement);
        tempElement.select();

        try {
            document.execCommand("copy");
            alert("Message copied to clipboard!");
        } catch (err) {
            console.error("Failed to copy message: ", err);
        }

        document.body.removeChild(tempElement);
    }
    </script>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def home():
    result = None
    error = None
    try:
        if request.method == 'POST':
            account_number = request.form.get('account_number')
            selected_database = request.form.get('database')

            if selected_database == 'old':
                result = generate_message(df_old_filtered, account_number)
            else:
                result = generate_message(df_latest_filtered, account_number)
    except Exception as e:
        error = f"Error: {str(e)}"
    return render_template_string(home_page, result=result, error=error)


# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name('cedar-gift-432307-k2-e107b6f6c67e.json', scope)
gc = gspread.authorize(credentials)
sheet = gc.open("FTDH LOGGED DISPUTES - STATUS BOARD").worksheet("Aug 2024")

# Load headers and data
headers = sheet.row_values(6)
headers = [header.strip() for header in headers]
data = sheet.get_all_values()[6:]
num_columns = len(headers)

if len(data[0]) != num_columns:
    data = [row[:num_columns] for row in data]

df = pd.DataFrame(data, columns=headers)

# Normalize function
def normalize(value):
    if pd.notna(value):
        return re.sub(r'\D', '', str(value))
    return ''

# Internal page template
internal_page = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Internal Lookup and Macro Generator</title>
    <style>
            .home-button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            font-size: 16px;
            border: none;
            cursor: pointer;
            border-radius: 8px;
            text-decoration: none;
            margin-top: 20px;
        }

        .home-button:hover {
            background-color: #45a049;
        }

        /* Center the button on the page */
        .center-container {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            flex-direction: column;
        }

        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-color: #f0f0f0;
        }
        .container {
            text-align: center;
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            max-width: 500px;
        }
        input[type="text"], input[type="number"], input[type="date"] {
            padding: 0.5rem;
            width: 100%;
            margin: 0.5rem 0;
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        input[type="submit"] {
            padding: 0.5rem 1rem;
            background-color: #28a745;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        input[type="submit"]:hover {
            background-color: #218838;
        }
        .result {
            margin-top: 1rem;
            font-size: 1.2rem;
        }
        .error {
            color: red;
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="home-button">Go Back to Home Page</a>
        <h1>Internal Layering Lookup and Macro Generator</h1>
            <h5 style="position: fixed; bottom: 10px; width: 100%; text-align: center; font-size: 0.75rem; color: #666;">Designed by RAWN</h5>

        <!-- Lookup Form -->
        <form action="/internal" method="post">
            <input type="text" name="lookup_number" placeholder="Enter number" required>
            <input type="submit" value="Lookup">
        </form>
        {% if lookup_result %}
            <div class="result">
                <h3>Lookup Result:</h3>
                <p>{{ lookup_result|safe }}</p>
            </div>
        {% endif %}
        
        <!-- Macro Generator Form -->
        <form action="/internal" method="post">
            <input type="text" name="sender" placeholder="Enter sender's number" required>
            <input type="number" name="amount" placeholder="Enter amount in PKR" required>
            <input type="date" name="date" required>
            <input type="submit" name="generate_macro" value="Generate Macro">
        </form>
        {% if macro %}
            <div class="result">
                <h3>Generated Macro:</h3>
                <p>{{ macro|safe }}</p>
            </div>
        {% endif %}
        
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}
    </div>
</body>
</html>
'''

# Route for the "Internal" page
@app.route('/internal', methods=['GET', 'POST'])
def internal():
    lookup_result = None
    macro = None
    error = None

    if request.method == 'POST':
        if 'lookup_number' in request.form:
            try:
                lookup_number = request.form.get('lookup_number')
                column_b = df.iloc[:, 1]
                column_c = df.iloc[:, 2]
                column_n = df.iloc[:, 13]

                normalized_lookup_number = re.sub(r'\D', '', lookup_number)
                df['Normalized_N'] = df.iloc[:, 13].apply(normalize)

                matching_rows = df[df['Normalized_N'].str.contains(normalized_lookup_number, na=False)]

                if not matching_rows.empty:
                    lookup_result = []
                    for index, row in matching_rows.iterrows():
                        value_b = row[column_b.name]
                        value_c = row[column_c.name]
                        value_n = row[column_n.name]

                        if pd.notna(value_b) or pd.notna(value_c) or pd.notna(value_n):
                            lookup_result.append(f"Dispute ID: {value_b}, Original SP User: {value_c}, Layering details: {value_n}")
                else:
                    error = "No matching number found in Column N."
            except Exception as e:
                error = str(e)

        elif 'generate_macro' in request.form:
            try:
                # Stage 3: Macro generation
                sender = request.form.get('sender')
                amount = request.form.get('amount')
                date = request.form.get('date')

                macro = f"""Internal Layering

Hey!

We received complaints for disputed transactions of PKR {amount} on {date} from {sender}.<br>

In accordance with industry-wide practice, we have deactivated your account until further notice. In the meanwhile, it would be really helpful if you could please provide us the following details:<br>

- Reason of transaction<br>
- Relationship with sender (if any)<br>
- Any proof you can provide that the transaction was genuine<br>
- A picture of your CNIC (both front and back)<br>

Thank you
"""
            except Exception as e:
                error = str(e)

    return render_template_string(internal_page, lookup_result=lookup_result, macro=macro, error=error)


if __name__ == '__main__':
    app.run(debug=True)
