import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from apps.account.models import User
from datetime import datetime

class Command(BaseCommand):
    help = 'Imports users from an Excel file into the User model.'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the Excel file containing user data.')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']

        try:
            # Load the Excel file into a pandas DataFrame with explicit engine
            df = pd.read_excel(file_path, engine='openpyxl', dtype=str)
        except Exception as e:
            raise CommandError(f"Error reading the Excel file: {e}")

        for index, row in df.iterrows():
            try:
                telephone = str(row['موبایل']).strip()
                if telephone.startswith('0'):
                    telephone = '+98' + telephone[1:]

                # Convert date format to YYYY-MM-DD
                # raw_date = row['تاریخ ایجاد']
                # try:
                #     formatted_date = datetime.strptime(raw_date, "%Y/%m/%d").strftime("%Y-%m-%d")
                # except ValueError:
                #     formatted_date = None
                    # raise ValueError(f"Invalid date format for 'تاریخ ایجاد' in row {index + 1}. Expected format: YYYY/MM/DD.")

                company_economic_number = str(row.get('کد اقتصادی', '')).strip()
                if pd.isna(company_economic_number) or not company_economic_number or company_economic_number == 'nan':
                    company_economic_number = None

                company_national_id = str(row.get('شناسه سازمان', '')).strip()
                if pd.isna(company_national_id) or not company_national_id or company_national_id == 'nan':
                    company_national_id = None


                # Map the Excel columns to User model fields
                user = User(
                    username=telephone,
                    first_name=row['نام '],
                    last_name=row['نام خانوادگی'],
                    address=row['آدرس'],
                    telephone=telephone,
                    email=row['ایمیل'],
                    national_id=row['کدملی'],
                    company_name=row.get('نام سازمان', None),
                    company_national_id=company_national_id,
                    company_economic_number=company_economic_number,
                    postal_code=row.get('کد پستی'),
                    educational_level_id=None,  # Example: Map based on your logic
                    educational_field_id=None,  # Example: Map based on your logic
                    user_type='customer',
                    account_type='business' if row.get('نوع شخصیت') == 'حقوقی' else 'personal',
                )

                user.set_password(row['کدملی'])

                user.save()

                self.stdout.write(self.style.SUCCESS(f"{index}: User {user.username} imported successfully."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"{index}: Error importing user at row {index}: {e}"))
