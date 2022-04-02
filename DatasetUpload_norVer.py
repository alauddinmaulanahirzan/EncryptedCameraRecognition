from mysql.connector import connect, Error # pip3 mysql-connector-python
import os

## Utils ##
def toBinary(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        binaryData = file.read()
    return binaryData
def toByte(data):
    return data.encode("utf-8")
## Utils ###

## Upload Func ##
def uploadData():
    try:
        connection = connect(host='192.168.0.62', # Pi-Server IP
                                             database='dataset',
                                             user='picam',
                                             password='picam')

        # Upload dengan Loop
        for dirname, dirnames, filenames in os.walk('data'):
            for filename in filenames:
                # Operasi File
                file = os.path.join(dirname, filename)
                folder = dirname.rsplit("/")[1]
                cursor = connection.cursor()

                # Enkripsikan File
                imgFile = toBinary(file)
                # Hash File Enkripsi
                imgHash = toHash(imgFile)

                # SQL String
                sql_insert = """INSERT INTO imageset_normal
                            (imgNama, imgFile) VALUES (%s,%s)"""

                # Konversi Data ke Tuple
                insert_data = (folder, imgFile)
                result = cursor.execute(sql_insert, insert_data)
                connection.commit()
                print("Insert Name "+folder+" : Success - Error : ", result)

    except Error as error:
        print("=> Upload Failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("=> Upload Finished")
## Upload Func ##

def main():
    print("> Upload Data Set")
    uploadData()


if __name__ == "__main__":
    main()
