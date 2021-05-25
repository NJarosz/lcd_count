import time
import csv
from datetime import datetime, date, timedelta
from mfrc522 import SimpleMFRC522
import I2C_LCD_driver
from gpiozero import Button, InputDevice, OutputDevice

with open("/etc/hostname", "r") as hn:
    pi = hn.readline().rstrip("\n")

shot_sig = Button(4)
button1 = Button(26)
button2 = Button(12)
sig_out = OutputDevice(17)
reader = SimpleMFRC522()
lcd = I2C_LCD_driver.lcd()
csv_path = "/home/pi/Documents/CSV/"
file_path = ""
logon = "LOG_ON"
logout = "LOG_OFF"
timeout = "TIME_OUT"
mas = "MAS"
mae = "MAE"
shot = "SHOT"
modes = {"setup": 0,
         "standby": 1,
         "menu": 2,
         "run": 3 ,
         "maint": 4
         }
mode = modes["setup"]
startup = True
count_path = "/home/pi/Documents/totalcount"
maint_msg = "Maintenance"
maint_end_msg = "Maintenance End"
invalid_msg = "Invalid Info"
menu_msg1 = "Setup Mode"
menu_msg2 = "Reset Counter"
count_reset = "Counter= 0"
logoutm = "Logged Out"
timeoutm = "Timed Out"


def set_part_mach():
    """Sets part number, machine number, and timeout duration"""
    file = "/home/pi/Desktop/main"
    with open(file, 'r') as text:
        for line in text:
            if len(line.strip()) == 0:      #skips any blank lines
                pass
            elif "#" in line:
                pass
            else:
                try:
                    key, value = line.replace(' ', '').strip().split(",")
                    key = key.lower()
                    if "part" in key:
                        part = value
                    elif "mach" in key:
                        mach = value
                except:
                    part, mach = None, None
    return part, mach



def evaluate(part, mach):
    b = False
    try:
        if part and len(part) != 0:
            if mach and len(mach) != 0:
                b = True
    except:
        b = False
    return b

def read_count(file=count_path):
    with open(file, "r", newline="") as f:
        total_count = f.readline()
        if len(str(total_count)) == 0:
            total_count = 0
        else:
            total_count = int(total_count)
    return total_count


def write_count(part_count, file=count_path):
    if part_count > 999999:
        part_count = 0
    with open(file, "w") as f:
        f.write(str(part_count))
                

def invalid_params():
    lcd.clear()
    lcd.message(invalid_msg)
    time.sleep(10)
    lcd.clear()


def create_file_path(day, path=csv_path):
    filename = day.strftime("%Y%m%d") + f"{pi}.csv"
    file_path = path + filename
    return file_path


def create_csv(file):
    """creates a new csv file, inserts a header"""
    with open(file, "a", newline="") as fa, \
            open(file, "r", newline='') as fr:
        writer = csv.writer(fa, delimiter=",")
        line = fr.readline()
        if not line:  # if CSV is empty, add header
            header = ("Type", "pi", "Machine", "Part",
                      "User_ID", "Time", "Date")
            writer.writerow(header)


def add_timestamp(cat, file):
    """opens or creates a csv file with todays date in
    filename. Adds timestamp to that csv including machine
    number, part number, id number, user, time, date"""
    now = time.strftime("%H:%M:%S")
    data = (cat, pi, mach_num, part_num, emp_num, now, today)
    with open(file, "a", newline="") as fa:
        writer = csv.writer(fa, delimiter=",")
        writer.writerow(data)
   
def update_csv():
    today = date.today()
    file_path = create_file_path(day=today)
    create_csv(file=file_path)
    return today, file_path
        
def display_run_info(last_display, last_disp_time):
    lcd.message(run_msg_btm, 2)
    if datetime.now() > last_disp_time + timedelta(seconds=5):
        if last_display != 1:
            lcd.message("                ",1)
            lcd.message(run_msg_top1, 1)
            last_display = 1
        else:
            lcd.message("                ",1)
            lcd.message(run_msg_top2, 1)
            last_display = 0
        last_disp_time = datetime.now()
    return last_display, last_disp_time

def change_msg(msg, sec=1, line=1):
    lcd.clear()
    lcd.message(msg, line)
    time.sleep(sec)


try:    
    while True:
        if mode == modes["setup"]:
            lcd.clear()
            lcd.message("Setup")
            while mode == modes["setup"]:
                part_num, mach_num = set_part_mach()
                test = evaluate(part_num, mach_num)
                if test is True:
                    total_count = read_count()
                    if startup is True:
                        today, file_path = update_csv()
                        mode = modes["standby"]
                    else:
                        #lcd.messsage = setup1_msg
                        time.sleep(.5)
                        keeplooping = True
                        endtlooptime = datetime.now() + timedelta(seconds=10)
                        while keeplooping == True and datetime.now() <= endtlooptime:
                            if button1.is_pressed:
                                button1.wait_for_release()
                                mode = modes["standby"]
                                keeplooping = False

                else:
                    invalid_params()
            startup = False
        elif mode == modes["standby"]:
            #empname = None
            emp_num = None
            idn = None
            lcd.clear()
            standby_info_top = f"{part_num} {mach_num}"
            standby_info_btm = f"Cnt:{total_count}"
            lcd.message(standby_info_top, 1)
            lcd.message(standby_info_btm, 2)
            while mode == modes["standby"]:
                if date.today() != today:
                    today, file_path = update_csv()
                idn, emp_num = reader.read_no_block()
                if emp_num != None:
                    emp_num = emp_num.strip()
                    if emp_num == '':
                        pass
                    else:
                        emp_count = 0
                        add_timestamp(logon, file_path)
                        mode = modes["run"]
                if button2.is_pressed:
                    button2.wait_for_release()
                    time.sleep(0.2)
                    mode = modes["menu"]
        elif mode == modes["menu"]:
            menu = 1
            lcd.clear()
            while mode == modes["menu"]:
                if menu == 1:
                    lcd.message(menu_msg1)
                    time.sleep(.5)
                    if button1.is_pressed:
                        button1.wait_for_release()
                        mode = modes["setup"]
                        break
                    if button2.is_pressed:
                        button2.wait_for_release()
                        menu = 2
                        lcd.clear()
                        lcd.message(menu_msg2)
                if menu == 2:
                    time.sleep(.5)
                    if button1.is_pressed:
                        button1.wait_for_release()
                        total_count = 0
                        write_count(part_count=total_count)
                        lcd.clear()
                        lcd.message(count_reset)
                        time.sleep(3)
                        mode = modes["standby"]
                        break
                    if button2.is_pressed:
                        button2.wait_for_release()
                        time.sleep(0.3)
                        menu = 1
                        lcd.clear()
        elif mode == modes["run"]:
            sig_out.on()
            run_msg_top1 = f"{part_num}  {mach_num}"
            run_msg_top2 = f"{emp_num}"
            last_display = 0
            now, last_disp_time = datetime.now(), datetime.now()
            lcd.clear()
            lcd.message(run_msg_top2, 1)
            while mode == modes["run"]:
                run_msg_btm = f"Cnt:{emp_count}, {total_count}"
                last_display, last_disp_time = display_run_info(last_display, last_disp_time)
                if shot_sig.is_pressed:
                    shot_sig.wait_for_release()
                    emp_count +=1
                    total_count +=1
                    write_count(part_count=total_count)
                    add_timestamp(shot, file_path)
                    now = datetime.now()
                    time.sleep(0.1)
                elif datetime.now() >= now + timedelta(seconds=300):
                    add_timestamp(timeout, file_path)
                    sig_out.off()
                    change_msg(timeoutm, sec=1)
                    mode = modes["standby"]
                if button1.is_pressed:
                    button1.wait_for_release()
                    add_timestamp(logout, file_path)
                    sig_out.off()
                    lcd.clear()
                    lcd.message(logoutm)
                    time.sleep(1)
                    mode = modes["standby"]
                if button2.is_pressed:
                    button2.wait_for_release()
                    sig_out.off()
                    mode = modes["maint"]
        elif mode == modes["maint"]:
            add_timestamp(mas, file_path)
            lcd.clear()
            lcd.message(maint_msg)
            time.sleep(1)
            while mode == modes["maint"]:
                if button1.is_pressed:
                    button1.wait_for_release()
                    add_timestamp(mae, file_path)
                    add_timestamp(logout, file_path)
                    lcd.clear()
                    lcd.message(logoutm)
                    time.sleep(1)
                    mode = modes["standby"]
                if button2.is_pressed:
                    button2.wait_for_release()
                    add_timestamp(mae, file_path)
                    lcd.clear()
                    lcd.message(maint_end_msg)
                    time.sleep(1)
                    mode = modes["run"]
except KeyboardInterrupt:
    lcd.clear()
except Exception as e:
    lcd.clear()
    lcd.message("ERROR")
