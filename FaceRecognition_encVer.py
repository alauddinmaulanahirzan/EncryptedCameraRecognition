# Database Connector
from mysql.connector import connect, Error  # pip3 mysql-connector-python
# Crypto Library
import hashlib
from Crypto.Cipher import AES
# Face Recognition Library
import face_recognition     # pip3 face_recognition
import cv2                  # python3-opencv / conda-forge opencv
import numpy as np
import imutils
from imutils.video import VideoStream   # pip3 imutils
from imutils.video import FPS
# Telegram Bot library
import logging
import os
import psutil       # pip3 psutil
# Additional Imports
import time
import sys
import pickle
import json
# RPi
import RPi.GPIO as GPIO
# Benchmark Module
from benchFile import *
from numpyencoder import NumpyEncoder

# Global Params
knownEncodings = []
knownNames = []
imageset = []
invalid_data = 0
title = "BenchEncrypt"
process = None

## Utils ##
def toBinary(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        binaryData = file.read()
    return binaryData

def toHash(data):
    return str(int(hashlib.sha1(str(data).encode("UTF-8")).hexdigest(), 16))[:16]

def toByte(data):
    return data.encode("utf-8")
## Utils ##

## Encrypt ##
def decryptImg(key, data, iv):
    byte_key = toByte(key)
    cipher = AES.new(byte_key, AES.MODE_CFB, iv=iv)
    original_data = cipher.decrypt(data)
    return original_data

def encryptImg(key,data):
    byte_key = toByte(key)
    cipher = AES.new(byte_key, AES.MODE_CFB) # CFB mode
    ciphered_data = cipher.encrypt(data) # Only need to encrypt the data, no padding required for this mode
    return ciphered_data,cipher.iv
## Decrypt ##

## Encoding ##
def encodeImg(key):
    global knownNames
    global knownEncodings
    count = 0
    for imagedata in imageset:
        name = imagedata[0]
        # Decrypt Image
        writeBenchmark(process,title,"Decrypt Image Before")
        imgFile = decryptImg(key, imagedata[1], imagedata[2])
        writeBenchmark(process,title,"Decrypt Image After")
        # Bytes to Image Numpy
        writeBenchmark(process,title,"Encode Image Before"+str(count))
        nparr = np.frombuffer(imgFile, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        # Face Box Recognition
        boxes = face_recognition.face_locations(
            rgb, model="hog")  # atau "hog" / "cnn"
        # Pemrosesan Wajah
        encodings = face_recognition.face_encodings(rgb, boxes)
        # Loop semua proses encoding
        for encoding in encodings:
            knownEncodings.append(encoding)
            knownNames.append(name)
        writeBenchmark(process,title,"Encode Image After"+str(count))
        count += 1

    data_image = {"encodings": knownEncodings, "names": knownNames}
    # Encrypt Pickle
    str_image = json.dumps(data_image,cls=NumpyEncoder)
    byte_data_image = toByte(str_image)
    writeBenchmark(process,title,"Encrypt Pickle Before")
    pickleData,pickleIV = encryptImg(key,byte_data_image)
    writeBenchmark(process,title,"Encrypt Pickle After")
    # Simpan Hasil Encoding ke Pickle
    f = open("encodedset_enc", "wb")
    f.write(pickle.dumps(pickleData))
    f.close()
    f = open("encodedset_iv", "wb")
    f.write(pickle.dumps(pickleIV))
    f.close()
## Encoding ##

## Recognition ##
def faceRecognition(key):
    image_data = pickle.loads(open("encodedset_enc", "rb").read())
    image_iv = pickle.loads(open("encodedset_iv", "rb").read())
    # Decrypt
    writeBenchmark(process,title,"Decrypt Pickle Before")
    image_data = decryptImg(key, image_data, image_iv)
    writeBenchmark(process,title,"Decrypt Pickle After")
    image_data = json.loads(image_data)
    detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
    writeBenchmark(process,title,"Face Recognition Before")
    # Start Camera
    vs = VideoStream(src=0).start()
    time.sleep(3.0)
    # FPS counts
    fps = FPS().start()
    recognize = False
    close_camera = False
    close_count = 0
    timeout = 0
    while close_camera == False:
        # Baca FPS
        frame = vs.read()
        frame = imutils.resize(frame, width=500)
        # Konversi ke grayscale dan konversi ke RGB
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Deteksi wajah dari frame grayscale
        rects = detector.detectMultiScale(gray, scaleFactor=1.1,
                                          minNeighbors=5, minSize=(30, 30),
                                          flags=cv2.CASCADE_SCALE_IMAGE)

        # Tampilkan kotak di wajah yang dideteksi
        boxes = [(y, x + w, y + h, x) for (x, y, w, h) in rects]

        encodings = face_recognition.face_encodings(rgb, boxes)
        names = []

        # Loop di semua wajah yang terdeteksi
        for encoding in encodings:
            matches = face_recognition.compare_faces(
                image_data["encodings"], encoding)
            name = "Unknown"

            # Cek apakah ada wajah yang dikenali
            if True in matches:
                matchedIdxs = [i for (i, b) in enumerate(matches) if b]
                counts = {}
                for i in matchedIdxs:
                    name = image_data["names"][i]
                    counts[name] = counts.get(name, 0) + 1
                name = max(counts, key=counts.get)
                recognize = True
            names.append(name)

        # Loop di semua wajah yang sudah dikenali
        for ((top, right, bottom, left), name) in zip(boxes, names):
            # tampilkan nama di wajah yang dikenali
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            y = top - 15 if top - 15 > 15 else top + 15
            cv2.putText(frame, name, (left, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

        # Tampilkan gambar di layar
        cv2.imshow("Mencari Wajah", frame)
        key = cv2.waitKey(1) & 0xFF

        # update FPS
        if(recognize == True):
            if(close_count == 10):
                close_camera = True
            else:
                close_count += 1
        elif(timeout < 60):
            timeout += 1
        elif(timeout == 60):
            break
        else:
            fps.update()

    # tampilkan info FPS
    fps.stop()
    # cleanup
    cv2.destroyAllWindows()
    vs.stop()
    time.sleep(2.0)
    writeBenchmark(process,title,"Face Recognition After")
    return recognize, fps
## Recognition ##

## Retrieve ##
def retrieveData():
    global invalid_data
    global imageset
    try:
        connection = connect(host='192.168.0.62',  # Pi-Server IP
                             database='dataset',
                             user='picam',
                             password='picam')
        cursor = connection.cursor()
        sql_retrieve = """SELECT * from imageset_encrypted"""
        cursor.execute(sql_retrieve)
        record = cursor.fetchall()
        for row in record:
            imgID = row[0]
            imgName = row[1]
            encImgFile = row[2]
            imgIV = row[3]
            imgHash = row[4]
            # Cek Validitas
            curHash = toHash(encImgFile)
            if(curHash != imgHash):
                invalid_data += 1
            # Simpan Data ke List
            retrieved_data = []
            retrieved_data.append(imgName)
            retrieved_data.append(encImgFile)
            retrieved_data.append(imgIV)        # Untuk Decrypt
            imageset.append(retrieved_data)
        if(invalid_data > 0):
            return False, invalid_data
        else:
            return True, invalid_data
    except Error as error:
        print("=> Gagal Mengambil Dataset {}".format(error))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
## Retrieve ##

## Door Mechanic ##
def unlockDoor():
    GPIO.setwarnings(False)
    pin = 21 #GPIO pin to connect to relay
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, True)

def lockDoor():
    GPIO.setwarnings(False)
    pin = 21 #GPIO pin to connect to relay
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, False)
## Door Mechanic ##

## Main Section
def main():
    # Get PID untuk Benchmark
    global process
    pid = os.getpid()
    process = psutil.Process(pid)
    # Create File dan Header
    createFile(title)
    # Main
    print("Face Detection Penelitian LPPM-2122")
    encoded_file = os.path.exists("encodedset_enc")
    encoded_iv = os.path.exists("encodedset_iv")
    key = "FTIKUSM-LPPM2122"
    if(encoded_file == False and encoded_iv == False):
        print("=> Mengambil Dataset dari DB")
        writeBenchmark(process,title,"DB Fetch Before")
        result, invalid_data = retrieveData()
        writeBenchmark(process,title,"DB Fetch After")
        print("=> Dataset Sukses Diunduh. Cek Validitas:")
        if(result == True):
            print("=> Dataset Gambar Valid")
            print("=> Memroses Dataset Gambar")
            encodeImg(key)  # Benchmark Insided
        else:
            print("=> "+invalid_data+" Data dari Dataset Gambar Tidak Valid")
            print("=> Membatalkan ...")
            sys.exit("Dataset Invalid Terdeteksi")
    print("=> Mendeteksi Gambar ...")
    result, fps = faceRecognition(key)  # Benchmark Inside
    if(result == True):
        print("=> Hasil : Wajah dikenali")
        print("==> Pintu : Membuka Kunci")
        unlockDoor()
        time.sleep(5)
        print("==> Pintu : Menutup Kunci")
        lockDoor()
        print("=> FPS elasped time: {:.2f}".format(fps.elapsed()))
        print("=> FPS approx. : {:.2f}".format(fps.fps()))
    else:
        print("=> Hasil : Wajah tidak terdeteksi - Timeout")
    print("=> Selesai")

if __name__ == "__main__":
    main()
