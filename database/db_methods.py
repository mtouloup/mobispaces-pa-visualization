import logging
import os.path
from configparser import ConfigParser
import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s :: %(levelname)s :: %(message)s')


class Connect:
    def __init__(self):
        """ Connect to the PostgreSQL database server """
        try:
            # read connection parameters
            params = config()

            # connect to the PostgreSQL server
            conn = psycopg2.connect(**params)

            # create a cursor
            cur = conn.cursor()
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(str(error))
        self.connection = conn
        self.cursur = cur


def config(filename='database.ini', section='postgresql'):
    path_current_directory = os.path.dirname(__file__)
    path_config_file = os.path.join(path_current_directory, 'database.ini')

    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(path_config_file)

    # get section, default to postgresql
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        logging.error(
            'Section {0} not found in the {1} file'.format(section, filename))
    return db

# This function returns an object of class Connect


def connection():
    return Connect()


def create_users_table():
    db = connection()

    """ create table in the PostgreSQL database"""
    command = (
        """
        CREATE TABLE IF NOT EXISTS users (
            email VARCHAR(255) NOT NULL PRIMARY KEY,
            password VARCHAR(255) NOT NULL
        )
        """)
    try:
        conn = db.connection
        cur = db.cursur
        cur = conn.cursor()
        # create table one by one
        cur.execute(command)
        # close communication with the PostgreSQL database server
        cur.close()
        # commit the changes
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(str(error))
    finally:
        if(connection):
            cur.close()
            conn.close()


def register_user(email,password):
    create_users_table()

    """ Insert into  table users """
    sql = """
            INSERT INTO users(email,password)
            VALUES(%s,%s)
        """
    try:
        # Prepare the connection
        db = connection()
        conn = db.connection
        cur = db.cursur

        record_to_insert = (email,password)
        cur.execute(sql, record_to_insert)

        conn.commit()

    except (Exception, psycopg2.Error) as error:
        if(connection):
            logging.error(str(error))
    finally:
        # closing database connection.
        if(connection):
            cur.close()
            conn.close()


def get_user(email=None, password=None):
    create_users_table()

    sql = """SELECT COUNT(*) FROM users where email=%s AND password=%s""" 

    try:
        db = connection()

        conn = db.connection
        cur = db.cursur
        cur = conn.cursor()

        cur.execute(sql, [email, password])
        
        result = cur.fetchone()
        # close communication with the PostgreSQL database server
        cur.close()
        # commit the changes
        conn.commit()

        return result[0]
    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(str(error))
    finally:
        if(connection):
            cur.close()

            conn.close()