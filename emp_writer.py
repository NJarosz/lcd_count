from mfrc522 import SimpleMFRC522
import I2C_LCD_driver
from gpiozero import Button, InputDevice, OutputDevice
import mysql.connector
from time import sleep


lcd = I2C_LCD_driver.lcd()
#lcd.color = [0,100,0]
reader=SimpleMFRC522()
conn = mysql.connector.connect(
                                host="10.0.0.167",
                                user="root",
                                passwd="gibson.88",
                                database="tjtest"
                            )
c = conn.cursor()

emp_num = input("Enter emp ID number: ")
lcd.clear()
print("Employee ID Number =", emp_num)
sleep(1.5)
emp_name = input("Enter emp name: ")
print("Employee Name =", emp_name)
sleep(1)
print("Please scan card.")
reader.write(emp_num)
card_id, emp_num_cd = reader.read()
print(card_id, emp_num_cd)
c.execute("REPLACE into employees (id, name, card_id_num) VALUES (%s,%s,%s)", (emp_num, emp_name, card_id))
conn.commit()
c.execute("SELECT * FROM employees")
print(c.fetchall())
c.close()
