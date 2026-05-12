import discord
from discord.ext import commands
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont


class Reservation: 
    '''def __init__(self, roomNumber: int, day: str, startTime: datetime, duration: int, user: discord.member.Member):
        self.roomNumber = roomNumber
        self.day = day
        self.startTime = startTime
        self.duration = duration
        self.bookman = None '''
    def __init__(self):
        self.bookman = None

class User:
    def __init__(self, user: discord.member.Member):
        self.user = user
        self.hours = 3
        self.blocked = False

class Calendar:
    SUCCESS = 0
    INVALID_DATE = -1
    INVALID_RESERVED = -2
    INVALID_DURATION = -3
    INVALID_CANCEL = -4
    RECORDING = "`recording`: GTMN"
    def __init__(self):
        self.booking_array = [] # 2 arrays representing booking slots for pr1 and pr2
        self.datetime_to_index = {} # datetime -> index
        self.users = {}  # discord handle -> user object
        self.daynums = {
            "monday" : 0,
            "tuesday" : 1,
            "wednesday" : 2,
            "thursday" : 3,
            "friday" : 4,
            "saturday" : 5,
            "sunday" : 6
        }
        self.initialize() # fills booking array and datetime index 

    
    def initialize(self):
        pr1_arr = []
        pr2_arr = []
        # monday 7:30 => monday 7:30
        # 7 days, 24 hours 7*24, 2 for 30 min intervals
        current = datetime.strptime("19:30", "%H:%M")
        day = current.day
        daycounter = 0
        for i in range(7*24*2):
            resv = Reservation()
            resv2 = Reservation()
            pr1_arr.append(resv)
            pr2_arr.append(resv2)
            currentday = current.day
            if (currentday != day):
                day = currentday
                daycounter += 1 
            self.datetime_to_index[(daycounter % 7, current.strftime("%I:%M %p"))] = i
            current += timedelta(minutes=30)
        self.booking_array.append(pr1_arr)
        self.booking_array.append(pr2_arr)

    def reserve(self, roomNumber: int, day: str, startTime: datetime, duration: float, user: discord.member.Member):
        if user not in self.users:
            userobj = User(user)
            self.users[user] = userobj
        
        if self.users[user].hours - duration < 0: #user does not have enough time to book
            return (self.INVALID_DURATION, None, None)
        timeindex = startTime.strftime("%I:%M %p")
        dayindex = self.daynums[day]
        roomindex = roomNumber - 1
        index = self.datetime_to_index[(dayindex, timeindex)]
        true_dur = int(duration*2)
        if (index + true_dur > len(self.booking_array[roomindex])):
            return (self.INVALID_DURATION, None, None)
        for offset in range(true_dur):
            if (self.booking_array[roomindex][index+offset].bookman != None):
                return (self.INVALID_RESERVED, self.booking_array[roomindex][index+offset].bookman, timeindex)
        for offset in range(true_dur):
            self.booking_array[roomindex][index+offset].bookman = user
        self.users[user].hours -= duration
        return (self.SUCCESS, None, None)

    def record(self, day: str, startTime: datetime, duration: float):
        timeindex = startTime.strftime("%I:%M %p")
        dayindex = self.daynums[day]
        index = self.datetime_to_index[(dayindex,timeindex)]
        true_dur = int(duration*2)
        print(true_dur)
        for offset in range(true_dur):
            #print(offset)
            if index+offset >= len(self.booking_array[0]):
                return
            self.booking_array[0][index+offset].bookman = self.RECORDING
            self.booking_array[1][index+offset].bookman = self.RECORDING
    
    def unrecord(self, day: str, startTime: datetime):
        timeindex = startTime.strftime("%I:%M %p")
        dayindex = self.daynums[day]
        index = self.datetime_to_index[(dayindex,timeindex)]
        print(index, self.booking_array[0][index])
        while(index < len(self.booking_array[0]) and self.booking_array[0][index].bookman == self.RECORDING):
            print(index, self.booking_array[0][index].bookman)
            self.booking_array[0][index].bookman = None
            self.booking_array[1][index].bookman = None
            index += 1

    
    def whohas(self, roomNumber: int, day: str, startTime: datetime):
        timeindex = startTime.strftime("%I:%M %p")
        dayindex = self.daynums[day]
        roomindex = roomNumber - 1
        index = self.datetime_to_index[(dayindex, timeindex)]
        return self.booking_array[roomindex][index].bookman
        '''if (roomNumber, day, current) not in self.calendarmap:
            print(self.calendarmap)
            return self.INVALID_DATE
        return self.calendarmap[(roomNumber, day, current)]'''
    
    def hours(self, user: discord.member.Member):
        '''if user not in self.usertime:
            return 3
        return 3 - self.usertime[user]'''
        if user not in self.users:
            userobj = User(user)
            self.users[user] = userobj

        return self.users[user].hours
    
    def cancel(self, roomNumber: int, day: str, startTime: datetime, user: discord.member.Member):
        timeindex = startTime.strftime("%I:%M %p")
        dayindex = self.daynums[day]
        roomindex = roomNumber - 1
        index = self.datetime_to_index[(dayindex, timeindex)]
        while index < len(self.booking_array[roomindex]) and self.booking_array[roomindex][index].bookman == user:
            self.booking_array[roomindex][index].bookman = None
            self.users[user].hours += 0.5
            index += 1
        if index == self.datetime_to_index[(dayindex, timeindex)]:
            return self.INVALID_CANCEL
        return self.SUCCESS
   
    def clear(self): 
        self.initialize()
        for user in self.users.values():
            user.hours = 3

    def generate_schedule_image(self, user: discord.member.Member):
        self.CELL_W = 40
        self.CELL_H = 30
        self.LEFT_PAD = 80
        self.TOP_PAD = 40

        DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun", "Mon"]

        cols = 48   
        rows = 8    

        width = self.LEFT_PAD + cols * self.CELL_W
        height = self.TOP_PAD + rows * self.CELL_H

        img = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arial.ttf", 14)
        except:
            font = None

        OFFSET = 39
        TOTAL_SLOTS = 7 * 48  # 336

        for day in range(rows):
            for slot in range(cols):

                index = day * 48 + slot - OFFSET


                if index < 0 or index >= TOTAL_SLOTS:
                    continue

                x = self.LEFT_PAD + slot * self.CELL_W
                y = self.TOP_PAD + day * self.CELL_H

                pr1 = self.booking_array[0][index].bookman
                pr2 = self.booking_array[1][index].bookman

                text = ""
                color = (240, 240, 240)

                if pr1 == user or pr2 == user:
                    text = "X"
                    if pr1 == user:
                        #color = (168,99,100)
                        color(100,200,150)
                    elif pr2 == user:
                        color = (106,188,226)
                
                elif pr1 == self.RECORDING or pr2 == self.RECORDING:
                    text = "R"
                    color = (255, 28, 239)

                elif pr1 and pr2:
                    text = "1&2"
                    color = (255, 255, 150)
                elif pr1:
                    text = "1"
                    color = (255, 180, 180)
                elif pr2:
                    text = "2"
                    color = (180, 180, 255)
                else:
                    color = (240, 240, 240)

                draw.rectangle([x, y, x + self.CELL_W, y + self.CELL_H], fill=color, outline="black")

                if text:
                    draw.text((x + 10, y + 5), text, fill="black", font=font)
        for i, day in enumerate(DAYS):
            y = self.TOP_PAD + i * self.CELL_H + 5
            draw.text((10, y), day, fill="black", font=font)

        start = datetime.strptime("00:00", "%H:%M")

        for i in range(0, 48, 2):
            t = (start + timedelta(minutes=30*i)).strftime("%I:%M")
            x = self.LEFT_PAD + i * self.CELL_W
            draw.text((x, 5), t, fill="black", font=font)

        img.save("schedule.png")