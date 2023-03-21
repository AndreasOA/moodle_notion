# Moodle Deadline Extractor and Notion Uploader

This Python project extracts upcoming deadlines from a University website called Moodle and uploads them to a Notion database as a ToDo List with Date, Title, and Course Name. The project utilizes the Selenium and requests Python libraries.

## Setup

To use this project, you will need to set up a Notion integration and obtain access tokens. You will also need to create a Notion database with the appropriate properties for the extracted deadline information.

1. Clone this repository to your local machine.
2. Install the required libraries (`Selenium`).
3. Obtain your Notion API key and database ID. See [Notion's documentation](https://developers.notion.com/docs/getting-started#step-2-share-a-database-with-your-integration) for more information.
4. Create a `credentials.json` file in the project's root directory with the following structure:
   ```json
    {
        "telegram": {
            "api_token": "XXXXXXX",
            "chat_id": "XXXXXXX",
            "phone": "XXXXXXX"
        },
        "moodle": {
            "username": "XXXXXXX",
            "password": "XXXXXXX"
        },
        "notion": {
            "token": "secret_XXXXXXX",
            "database_id": "XXXXXXX"
        },
        "chrome": {
            "chrome_profile": "XXXXXXX"
        }
    }
    ```
5. Replace all `XXXXXXX` with your own values obtained from Notion, Moodle and Telegram.
6. If you want to use your own chrome profile to have access to your cookies add the profile path.
7. Run the moodle_read_sel.py file to extract deadlines from Moodle and upload them to Notion.

## Usage
To run the project, simply execute the moodle_read_sel.py file in your environment.

The program will use Selenium to open a web browser and log into the University's Moodle website with the provided username and password in credentials.json. It will then extract the upcoming deadlines from the website's "Upcoming events" block. It is possible that you have to change the path to the chromdriver executable.

The extracted deadlines will be uploaded to a Notion database as a ToDo List with properties for Date, Title, and Course Name.

## Dependencies
- Python 3.6+
- Selenium
- Requests