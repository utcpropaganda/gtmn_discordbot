import discord
from discord.ext import commands
from datetime import datetime
from reservations import Reservation, Calendar
import difflib
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='>', intents=intents)

PR_ACCESS_ROLE_ID = 1489290466573947033
ADMIN_ROLE_ID =1489297257785463035
# might have to have a general officer role, maybe admin role

phelpstring = "Here are the available commands:\n\t!reserve <roomNumber> <day> <startTime> <duration>: To reserve a room.\n\t!cancel <roomNumber> <day> <startTime>: To cancel a reservation from a given startTime. \n\t!cancel all: Cancel all of your reservations without specifying a time\n\t!display: To display the schedule.\n\t!whohas <roomNumber> <day> <time>: To display who is using a room at a given time.\n\t!raid <day> <startTime> <duration>: To mark equipment as removed (Officers only).\n\t!unraid <day> <startTime>: To remove raid mark (Officers only).\n\t!record <day> <startTime> <duration>: To add a recording session (Officers only).\n\t!unrecord <day> <startTime>: To cancel a recording session (Officers only).\n\t!hours: To see how many remaining hours you can reserve this week\n\t!phelp: To display this message.\nWhat the display colors mean:"
days = {'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday','sunday'}

calendar = Calendar()

def has_access(user):
	return user.get_role(PR_ACCESS_ROLE_ID) != None

def is_admin(user):
	return user.get_role(ADMIN_ROLE_ID) != None

def format_userid(uid):
	return uid[2:-1]


# ADMIN COMMANDS

@bot.command()
async def record(ctx, day: str, startTime: str, duration: float):
	if (not is_admin(ctx.message.author)):
		return
	current = datetime.strptime(startTime, "%I:%M%p")
	day = day.lower()
	calendar.record(day, current, duration)
	await ctx.send('record not implemented')
@record.error
async def record_error(ctx, err):
	if isinstance(err, commands.MissingRequiredArgument):
		await ctx.send(f'{ctx.message.author.mention} format for !record is !record <day> <startTime> <duration>')
	else:
		await ctx.send(f'{err} {ctx.message.author.mention} room number and duration must be numbers.')

@bot.command()
async def unrecord(ctx, day, startTime):
	if (not is_admin(ctx.message.author)):
		return
	current = datetime.strptime(startTime, "%I:%M%p")
	calendar.unrecord(day, current)
	await ctx.send('unrecord not implemented')

@bot.command()
async def clear(ctx):
	if (not is_admin(ctx.message.author)):
		return
	await ctx.send("are you sure? type `yes` to confirm")
	def check(message):
		return (message.author == ctx.author and message.channel == ctx.channel)
	try:
		msg = await bot.wait_for("message", timeout=15.0, check=check)
		if msg.content.lower() == "yes":
			await ctx.send("clear not implemented")
		else:
			await ctx.send("clear cancelled")
	except:
		await ctx.send("clear command timed out")

@bot.command()
async def give_access(ctx, userid):
	if (not is_admin(ctx.message.author)):
		return
	user = await ctx.guild.fetch_member(format_userid(userid))
	if has_access(user):
		await ctx.send('user already has access')
		return
	role = ctx.guild.get_role(PR_ACCESS_ROLE_ID)
	await user.add_roles(role)
	await ctx.send('user now has access')

@bot.command()
async def remove_access(ctx, userid):
	if (not is_admin(ctx.message.author)):
		return
	user = await ctx.guild.fetch_member(format_userid(userid))
	role = user.get_role(PR_ACCESS_ROLE_ID)
	if not role:
		await ctx.send('user does not have pr access')
		return
	await user.remove_roles(role)
	await ctx.send('user now lost access')


# USER COMMANDS

@bot.command()
async def ping(ctx):
	print(has_access(ctx.message.author))
	#print(ctx.message.guild.roles)
	await ctx.send('pong')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        commands_list = [cmd.name for cmd in bot.commands]
        closest = difflib.get_close_matches(ctx.invoked_with, commands_list, n=1)

        if closest:
            new_command = closest[0]
            prefix = ctx.prefix
            rest = ctx.message.content[len(prefix + ctx.invoked_with):]
            new_content = f"{prefix}{new_command}{rest}"
            ctx.message.content = new_content
            await ctx.send(f"{ctx.author.mention} autocorrected to `{new_command}`")
            await bot.process_commands(ctx.message)
        else:
            await ctx.send(f"{ctx.author.mention}, not a command, type !phelp for a list of")

@bot.command()
async def phelp(ctx):
	if (not has_access(ctx.message.author)):
		return
	file = discord.File("calendarcolorlegend.png",filename="calendarcolorlegend.png")
	await ctx.send(phelpstring, file=file)

@bot.command()
async def whohas(ctx, roomNumber: int, day: str, startTime: str):
	if (not has_access(ctx.message.author)):
		return
	try:
		if roomNumber != 2 and roomNumber != 1:
			await ctx.send(f'{ctx.message.author.mention} <roomNumber> must be either 1 or 2, representing pr1 and pr2')
			return
		day = day.lower()
		if day not in days:
				await ctx.send(f"{ctx.message.author.mention} <day> must be name of day (Monday -> Sunday), isn't case sensitive")
				return 
		current = datetime.strptime(startTime, "%I:%M%p")
		ret = calendar.whohas(roomNumber, day, current)
		if ret == calendar.INVALID_DATE:
			await ctx.send(f'{ctx.message.author.mention} you entered an invalid time (HH:00 or HH:30)')
		elif ret == None:
			await ctx.send(f'{ctx.message.author.mention} no one has this room reserved')
		else:
			await ctx.send(f'{ctx.message.author.mention} {ret} has this room reserved')
	except ValueError:
		await ctx.send(f'{ctx.message.author.mention} <startTime> must be in the format of H:Mp, H = hour (1-12), M = minutes(00 or 30), p = AM/PM')
@whohas.error
async def whohas_error(ctx, err):
	if isinstance(err, commands.MissingRequiredArgument):
		await ctx.send(f'{ctx.message.author.mention} format for !whohas is !whohas <roomNumber> <day> <startTime>')
	else:
		await ctx.send(f'{ctx.message.author.mention} room number and duration must be numbers')

@bot.command()
async def hours(ctx):
	if (not has_access(ctx.message.author)):
		return
	ret = calendar.hours(ctx.message.author)
	await ctx.send(f'{ctx.message.author.mention} you have {ret} hours left to reserve')

@bot.command()
async def reserve(ctx, roomNumber: int, day: str, startTime: str, duration: float): # i probably have to flush reserve times before 7:30 monday!
	if (not has_access(ctx.message.author)):
		return
	try:
		if roomNumber != 2 and roomNumber != 1:
			await ctx.send(f'{ctx.message.author.mention} <roomNumber> must be either 1 or 2, representing pr1 and pr2')
			return
		day = day.lower()
		if day not in days:
			await ctx.send(f'{ctx.message.author.mention} <day> must be name of day (Monday -> Sunday), isn\'t case sensitive')
			return 
		current = datetime.strptime(startTime, "%I:%M%p")
		if (duration * 10)%5 != 0 or duration == 0:
			await ctx.send(f'{ctx.message.author.mention} duration can only be in increments of .5 [.5, 1, 1.5 ... 3]')
			return 
		if (duration > 3):
			await ctx.send(f'{ctx.message.author.mention} you cannot reserve more than 3 hours this week')
		if not duration: #check between current duration and duration, if current duration is >=3 or duration - current duration idk need to consider it
			await ctx.send(f'{ctx.message.author.mention} you do not have {duration} hours to use')
			return 
		
		#reservation = Reservation(roomNumber, day, startTime, duration, ctx.message.author)
		code, user, timestamp = calendar.reserve(roomNumber, day, current, duration, ctx.message.author)

		if code == Calendar.INVALID_DATE:
			await ctx.send(f'{ctx.message.author.mention} you have entered an invalid date')
			return
		if code == Calendar.INVALID_RESERVED:
			await ctx.send(f'{ctx.message.author.mention} time already reserved by {user}')
			return
		if code == Calendar.INVALID_DURATION:
			await ctx.send(f'{ctx.message.author.mention} you don\'t have {duration} hours left')
			return
		if code != Calendar.SUCCESS:
			await ctx.send(f'{ctx.message.author.mention}, error reserving')
			return 
		await ctx.send(f'{ctx.message.author.mention}, successfully reserved: {roomNumber} {day} {startTime} {duration}')
	except ValueError:
		await ctx.send(f'{ctx.message.author.mention} <startTime> must be in the format of H:Mp, H = hour (1-12), M = minutes, p = AM/PM')
@reserve.error
async def reserve_error(ctx, err):
	if isinstance(err, commands.MissingRequiredArgument):
		await ctx.send(f'{ctx.message.author.mention} format for !reserve is !reserve <roomNumber> <day> <startTime> <duration>')
	else:
		await ctx.send(f'{err} {ctx.message.author.mention} room number and duration must be numbers.')

@bot.command()
async def display(ctx):
	if (not has_access(ctx.message.author)):
		return
	calendar.generate_schedule_image(ctx.message.author)
	file = discord.File("schedule.png",filename="schedule.png")
	# have to make a file that saves as requests? idk
	# svg with squares corresponding to times, colors r the only dynamic thing
	await ctx.send(f'{ctx.message.author.mention}', file=file)

@bot.command()
async def cancel(ctx, roomNumber: int, day: str, startTime: str):
	if (not has_access(ctx.message.author)):
		return
	try:
		if roomNumber != 2 and roomNumber != 1:
			await ctx.send(f'{ctx.message.author.mention} <roomNumber> must be either 1 or 2, representing pr1 and pr2')
			return
		day = day.lower()
		if day not in days:
			await ctx.send(f'{ctx.message.author.mention} <day> must be name of day (Monday -> Sunday), isn\'t case sensitive')
			return 
		current = datetime.strptime(startTime, "%I:%M%p")
		
		#reservation = Reservation(roomNumber, day, startTime, duration, ctx.message.author)
		code = calendar.cancel(roomNumber, day, current,  ctx.message.author)

		if code != Calendar.SUCCESS:
			await ctx.send(f'{ctx.message.author.mention}, error cancelling: you do not have this time reserved')
			return 
		await ctx.send(f'{ctx.message.author.mention}, successfully cancelled')
	except ValueError:
		await ctx.send(f'{ctx.message.author.mention} <startTime> must be in the format of H:Mp, H = hour (1-12), M = minutes, p = AM/PM')
@cancel.error
async def cancel_error(ctx, err):
	if isinstance(err, commands.MissingRequiredArgument):
		await ctx.send(f'{ctx.message.author.mention} format for !cancel is !cancel <roomNumber> <day> <startTime>')
	else:
		await ctx.send(f'{err} {ctx.message.author.mention} room number must be a number.')

#@bot.command()

#@bot.command()

#@bot.command()

bot.run(os.getenv("DISCORD_TOKEN"))

'''
Here are the available commands:
!reserve <roomNumber> <day> <startTime> <duration>: To reserve a room.
!cancel <roomNumber> <day> <startTime>: To cancel a reservation.
!display: To display the schedule.
!whohas <roomNumber> <day> <time>: To display who is using a room at a given time.
!raid <day> <startTime> <duration>: To mark equipment as removed (Officers only).
!unraid <day> <startTime>: To remove raid mark (Officers only).
!record <day> <startTime> <duration>: To add a recording session (Officers only).
!unrecord <day> <startTime>: To cancel a recording session (Officers only).
!phelp: To display this message.
'''

'''
pr access role needs to be checked
yeah
'''
