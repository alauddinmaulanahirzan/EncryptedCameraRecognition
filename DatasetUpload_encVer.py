from mysql.connector import connect, Error # pip3 mysql-connector-python
import hashlib
import os
from Crypto.Cipher import AES

## Utils ##
def toBinary(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        binaryData = file.read()
    return binaryData

def toHash(data):
    return str(int(hashlib.sha1(str(data).encode("UTF-8")).hexdigest(),16))[:16]

def toByte(data):
    return data.encode("utf-8")
## Utils ###

## Encrypt ##
def encryptImg(key,data):
    byte_key = toByte(key)
    cipher = AES.new(byte_key, AES.MODE_CFB) # CFB mode
    ciphered_data = cipher.encrypt(data) # Only need to encrypt the data, no padding required for this mode
    return ciphered_data,cipher.iv
## Encrypt ##

## Upload Func ##
def uploadData(key):
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
                encImgFile,imgIV = encryptImg(key,imgFile)
                # Hash File Enkripsi
                imgHash = toHash(encImgFile)

                # SQL String
                sql_insert = """INSERT INTO imageset_encrypted
                            (imgNama, imgFile, imgIV, imgHash) VALUES (%s,%s,%s,%s)"""

                # Konversi Data ke Tuple
                insert_data = (folder, encImgFile, imgIV, imgHash)
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
    key = "FTIKUSM-LPPM2122"
    uploadData(key)


if __name__ == "__main__":
    main()
