

### IMPORTING
import os, datetime, configparser
import oracledb


### GLOBALS
MODULE_DIR = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
SW_DIR=os.path.dirname(MODULE_DIR)
config = configparser.ConfigParser()
config.read(os.path.join(SW_DIR,'config.ini'))
PATH_DB_KEYS=MODULE_DIR
USER = config['DATABASE']['USER']
PASSWORD = config['DATABASE']['PASS']
DNS = config['DATABASE']['DNS']
WALLET_PASSWORD = config['DATABASE']['WALLET_PASSWORD']


### CLASSES
class DataBase():
	
	def __init__(self):
		self.connection = None
		self.connection = oracledb.connect(config_dir=PATH_DB_KEYS,
									user=USER,
									password=PASSWORD,
									dsn=DNS,
									wallet_location=PATH_DB_KEYS,
									wallet_password=WALLET_PASSWORD)

	def query(self, sql,**kwargs):
		cursor = self.connection.cursor()
		cursor.execute(sql,**kwargs)
		return cursor
	
	def close_connection(self):
		self.connection.close()
		
	def get_list_guild_infos(self):
		list_guild_infos=[]
		cursor = self.query(f"SELECT * FROM CHANNELS")
		for row in cursor:
			list_guild_infos+=[{
				'guild_id': row[0],
				'guild_name': row[1],
				'channel_id': row[2],
				'channel_name': row[3],
				'author_id': row[4],
				'author': row[5]
			}]
		return list_guild_infos
			
	def print_table(self):
		cursor = self.query(f"SELECT * FROM CHANNELS")
		print('\nElements in the table CHANNELS:')
		for row in cursor:
			print("    > " + str(row))
		cursor.close()

	def insert(self, guild_infos:dict):
		sql = """INSERT INTO CHANNELS VALUES (:guild_id, :guild_name, :channel_id, :channel_name, :author_id, :author)"""
		try:
			cursor=self.query(sql,
						   guild_id=guild_infos.get('guild_id'),
						   guild_name=guild_infos.get('guild_name'),
						   channel_id=guild_infos.get('channel_id'),
						   channel_name=guild_infos.get('channel_name'),
						   author_id=guild_infos.get('author_id'),
						   author=guild_infos.get('author'))
			self.connection.commit()
			cursor.close()
			print('\nNew channel added: ','\n    >',guild_infos)
		except:
			print('\nError inserting: ','\n    >',guild_infos)

			
	def upsert(self,guild_infos:dict):
		sql="""
MERGE INTO CHANNELS ch 
   USING (SELECT :guild_id 		AS GUILD_ID,
                 :guild_name 	AS GUILD_NAME,
                 :channel_id 	AS CHANNEL_ID,
                 :channel_name 	AS CHANNEL_NAME,
                 :author_id 	AS AUTHOR_ID,
                 :author 		AS AUTHOR FROM DUAL) nr
   ON (ch.GUILD_ID = nr.GUILD_ID)
WHEN MATCHED THEN UPDATE
SET ch.GUILD_NAME 	= nr.GUILD_NAME,
    ch.CHANNEL_ID 	= nr.CHANNEL_ID,
    ch.CHANNEL_NAME = nr.CHANNEL_NAME,
    ch.AUTHOR_ID 	= nr.AUTHOR_ID,
    ch.AUTHOR 		= nr.AUTHOR
WHEN NOT MATCHED THEN INSERT
    (ch.GUILD_ID, ch.GUILD_NAME, ch.CHANNEL_ID, ch.CHANNEL_NAME, ch.AUTHOR_ID, ch.AUTHOR)
    VALUES (nr.GUILD_ID, nr.GUILD_NAME, nr.CHANNEL_ID, nr.CHANNEL_NAME, nr.AUTHOR_ID, nr.AUTHOR)
"""
		try:
			cursor=self.query(sql,
						   guild_id=guild_infos.get('guild_id'),
						   guild_name=guild_infos.get('guild_name'),
						   channel_id=guild_infos.get('channel_id'),
						   channel_name=guild_infos.get('channel_name'),
						   author_id=guild_infos.get('author_id'),
						   author=guild_infos.get('author'))
			self.connection.commit()
			cursor.close()
			print('\nNew channel upserted: ','\n    >',guild_infos)
		except:
			print('\nError inserting: ','\n    >',guild_infos)

	def get_channel_id(self,guild_id:int):
		sql="""SELECT CHANNEL_ID FROM CHANNELS WHERE GUILD_ID = :guild_id"""

		try:
			cursor=self.query(sql,
							  guild_id=guild_id)
			self.connection.commit()
			fetch = cursor.fetchone()
			cursor.close()
			return fetch[0] if fetch else None
		except Exception as e:
			print(f"\nError getting channel id with guild_id: {guild_id}. Description: ",e)
			return None
			
### MAIN
if __name__ == '__main__':
	
	# Open image of database
	db = DataBase()

	# Get all elements
	db.print_table()
	# list_guild_infos = db.get_list_guild_infos()
	
	# Insert fake channel
	guild_infos = {
		'guild_id': 11,
		'guild_name': 'aa',
		'channel_id': 2,
		'channel_name': 'b',
		'author_id': None,
		'author': 'c'}
	db.insert(guild_infos)
	db.print_table()
	
	# Test UPSERT
	db.upsert(guild_infos)
	db.print_table()

	# Test select channel_id
	channel_id=db.get_channel_id(guild_id=1)
	
	# Close connection when operations are done
	db.close_connection()