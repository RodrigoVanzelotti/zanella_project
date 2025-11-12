import os
import csv
from io import StringIO
from typing import Optional, List
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.services.di.container import get_config_service


class GoogleSheetsService:
    """
    Read-only service for fetching data from Google Sheets.
    Uses OAuth2 credentials from credentials.json file.
    """

    def __init__(self):
        config_service = get_config_service()
        self.scopes = config_service.get().google.scopes
        self.credentials_file = os.path.join(
            os.path.dirname(__file__),
            '..', '..', '..',
            'credentials.json'
        )
        self.token_file = os.path.join(
            os.path.dirname(__file__),
            '..', '..', '..',
            'token.json'
        )
        self._credentials = None
        self._drive_service = None
        self._sheets_service = None

    def _authenticate(self) -> None:
        """Authenticate with Google Sheets API using OAuth2 credentials."""
        if self._credentials is None:
            creds = None

            # Load token if it exists
            if os.path.exists(self.token_file):
                creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)

            # Refresh or create new credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file,
                        self.scopes
                    )
                    creds = flow.run_local_server(port=0)

                # Save credentials for future use
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())

            self._credentials = creds
            self._drive_service = build("drive", "v3", credentials=self._credentials)
            self._sheets_service = build("sheets", "v4", credentials=self._credentials)

    def fetch_spreadsheet_rows(
        self,
        spreadsheet_name: str,
        skip_initial_rows: int = 0,
        skip_final_rows: int = 0
    ) -> dict[str, List[List[str]]]:
        """
            Fetches all data from a Google Spreadsheet by name and returns a dictionary
            with sheet names as keys and lists of rows for each sheet. Each row is represented as a list of strings.

            Args:
                spreadsheet_name: The exact name of the Google Spreadsheet to search for.
                skip_initial_rows: Number of rows to skip from the beginning of each sheet (default: 0).
                skip_final_rows: Number of rows to skip from the end of each sheet (default: 0).

            Returns:
                dict[str, List[List[str]]]: Dictionary mapping sheet names to their rows as lists of strings.
                            Returns empty dict if spreadsheet not found.

            Raises:
                Exception: If there's an error accessing the Google Sheets API.
            """
        # Ensure authentication
        self._authenticate()

        try:
            # Step 1: Search for the spreadsheet by name in Drive
            query = f"name = '{spreadsheet_name}' and mimeType='application/vnd.google-apps.spreadsheet'"
            results = self._drive_service.files().list(
                q=query,
                fields="files(id, name)"
            ).execute()
            files = results.get("files", [])

            if not files:
                return {}  # Return empty dict if not found

            # Step 2: Get spreadsheet metadata
            spreadsheet_id = files[0]["id"]
            spreadsheet = self._sheets_service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            sheet_list = spreadsheet.get("sheets", [])

            sheets_dict = {}

            # Step 3: Loop through each sheet and load its contents
            for sheet in sheet_list:
                sheet_title = sheet["properties"]["title"]
                range_name = f"{sheet_title}"

                result = self._sheets_service.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id,
                    range=range_name
                ).execute()

                rows = result.get("values", [])

                if not rows:
                    # Add empty CSV for empty sheets
                    sheets_dict[sheet_title] = None
                    continue

                # Apply row truncation
                total_rows = len(rows)
                start_index = skip_initial_rows
                end_index = total_rows - skip_final_rows

                # Ensure valid indices
                if start_index < 0:
                    start_index = 0
                if end_index > total_rows:
                    end_index = total_rows
                if start_index >= end_index:
                    # All rows are skipped
                    sheets_dict[sheet_title] = None
                    continue

                sheets_dict[sheet_title] = rows[start_index:end_index]

            return sheets_dict

        except HttpError as error:
            raise Exception(f"Error fetching spreadsheet '{spreadsheet_name}': {error}")