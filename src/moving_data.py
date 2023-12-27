from twilio.rest import Client
from sqlalchemy import create_engine
import pymysql
import os
import pandas as pd
import datetime as dt


class DB:
    """

    """

    def __init__(self, force_env=None):
        super().__init__(force_env)
        self.date_ = dt.strftime(dt.now(), "%Y-%m-%d")

    def db_connect(self):
        return pymysql.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_DATABSE"))

    def make_engine(self, echo=True):
        mydbstr = """mysql+pymysql://{}:{}@{}:{}/{}"""
        return create_engine(
            mydbstr.format(
                os.getenv("DB_USER"),
                os.getenv("DB_PASSWORD"),
                os.getenv("DB_HOST"),
                str(os.getenv("DB_PORT")),
                os.getenv("DB_DATABSE")
            ), echo=echo
        )

    def from_db(self, query, parse_dates=None):
        conn = self.db_connect()
        df = pd.read_sql(query, conn, parse_dates=parse_dates)
        conn.commit()
        conn.close()
        return df

    def to_db(self, df, table, if_exists='append'):
        print('executing sql...')
        engine = self.makeEngine()
        df.to_sql(table, con=engine, if_exists=if_exists, index=False)
        print('closing engine')
        engine.dispose()
        print('done')

    def q(self, q):
        conn = self.db_connect()
        cursor = conn.cursor()
        cursor.execute(q)
        conn.commit()
        cursor.close()
        conn.close()


class Texto:
    def __init__(self):
        self.client = Client(os.getenv('TWILIO_SID'), os.getenv("TWILIO_AUTH"))
        return

    def send(self, row_data):
        payload = "\n".join(
            [self.row_for_text(r) for r in self.row_data]
        )
        payload = "*** NEW SENATE PTR***\n" + payload
        self.sendText(payload)

    def row_for_text(self, row):
        return ' '.join([
            row['Name (First)'].strip(),
            row['Name (Last)'].strip(),
            row['Filing Date'].strftime("%Y-%m-%d"),
            row['Filing Code'][-1]
        ])

    def send_text(self, payload=''):
        """

        """
        print('sending a text!')
        outgoing_phone_number = os.getenv("OUTGOING_PHONE_NUMBER", "pee")
        phone_numbers = os.getenv("PHONE_NUMBERS", "poop")
        if isinstance(phone_numbers, str):
            phone_numbers = eval(phone_numbers)

        elif isinstance(phone_numbers, int):
            phone_numbers = [str(phone_numbers)]

        print(outgoing_phone_number, phone_numbers)
        sent_messages = []
        for n in phone_numbers:
            print(phone_numbers)
            message = self.client.messages.create(
                body=payload,
                from_=outgoing_phone_number,
                to=n
                )
            sent_messages.append(message)
        return sent_messages
