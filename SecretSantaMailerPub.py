#------------------------------------------------------------------------
# Author:   Will Miller
# Created:
# Description:
#------------------------------------------------------------------------
import argparse
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def print_red(line):
    print("%s%s%s" % (tcolor.red, line, tcolor.reset))
    return

def print_green(line):
    print("%s%s%s" % (tcolor.green, line, tcolor.reset))
    return

def print_blue(line):
    print("%s%s%s" % (tcolor.blue, line, tcolor.reset))
    return

def print_debug(line):
    if args.debug:
        print("DEBUG: %s" % (line))
    return

class tcolor:
    red = '\033[31m'
    green = '\033[32m'
    blue = '\033[34m'
    light_green = '\033[92m'
    light_blue = '\033[94m'
    reset = '\033[0m'

    bg_red = '\033[41m'
    bg_green = '\033[42m'
    bg_blue = '\033[44m'
    bg_default = '\033[49m'

def sendEmail(sender_email, receiver_email, password, subject, body, smtp_server="smtp.gmail.com", port=587):
    """
    Sends an email using the specified SMTP server.
    
    Parameters:
        sender_email (str): The sender's email address.
        receiver_email (str): The recipient's email address.
        password (str): The sender's email password or app password.
        subject (str): The subject of the email.
        body (str): The body of the email.
        smtp_server (str): The SMTP server to connect to. Default is "smtp.gmail.com".
        port (int): The port to connect to the SMTP server. Default is 587.
    """
    try:
        # Create the email
        message = MIMEMultipart()
        #message["From"] = sender_email
        message["From"] = "Miller Secret Santa <no_reply@northpole>"
        message["To"] = receiver_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))
        
        # Connect to the SMTP server and send the email
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls()  # Upgrade the connection to secure
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

class GameConfig:
    def __init__(self, num_gifts, dev_email, dev_email_app_pass):
        self.num_gifts = num_gifts
        self.dev_email = dev_email
        self.dev_email_app_pass = dev_email_app_pass

class PlayerConfig:
    def __init__(self, player_list, couple_mapping, player_emails):
        if not isinstance(player_list, list):
            raise TypeError("player_list must be a list")
        if not isinstance(couple_mapping, dict):
            raise TypeError("couple_mapping must be a dict")
        if not isinstance(player_emails, dict):
            raise TypeError("player_emails must be a dict")

        self.players = player_list
        self.couples = couple_mapping
        self.player_emails = player_emails
        self.validate_config()

    def validate_config(self):
        if len(self.players) < 1:
            raise RuntimeError(f"Provided list of players is less than 1. Must contain 2 or more players.")
        
        # Make sure every player has an email
        number_of_players = len(self.players)
        if number_of_players != len(self.player_emails):
            raise RuntimeError(f"Number of emails ({len(self.player_emails)}) does not match"
                               f" number of players ({number_of_players})")
        for player in self.players:
            if player not in self.player_emails:
                raise RuntimeError(f"Failed to find email for player '{player}'")
        
        # Make sure the couples listed exist in the player list
        for partner_one, partner_two in self.couples.items():
          if partner_one not in self.players:
              raise RuntimeError(f"Failed to find {partner_one} in list of players when checking couples.")
          if partner_two not in self.players:
              raise RuntimeError(f"Failed to find {partner_two} in list of players when checking couples.")

class SecretSanta:
    def __init__(self, player_config, game_config):
        self.players = player_config.players
        self.couples = player_config.couples
        self.playerEmails = player_config.player_emails
        self.game_config = game_config

    def setupEmail(self, email_addr, subject, body):
        # Determine whether to send email to everybody or just the dev
        if args.production:
            target_email = email_addr
            print_blue("Sending email to %s" % (email_addr))
        else:
            dev_email = self.game_config.dev_email
            print_blue("Would have sent email to %s, instead its being sent to %s" % (email_addr, dev_email))
            target_email = dev_email
        
        # Actually send the email
        sendEmail(
            sender_email=self.game_config.dev_email,
            password=self.game_config.dev_email_app_pass,  # Using an app password for gmail
            receiver_email=target_email,
            subject=subject,
            body=body
        )

    def solve(self):
        solved = self.findMatches()
        while not solved:
            solved = self.findMatches()

        if not args.production:
            #Print final results
            print_green("Final Matches:")
            for player in self.finalMatches:
                print_blue("  %s gets %s" % (player, ",".join(self.finalMatches[player])))

    def findMatches(self):
        #populate final list of matches
        self.finalMatches = dict()
        for playerName in self.players:
            self.finalMatches[playerName] = list()

        #Choose random secret santa
        maxDraftRounds = self.game_config.num_gifts
        for draftRound in range(0,maxDraftRounds):
            takenPlayers = list()
            print_debug("Round %d" % (draftRound))

            for playerName in self.players:
                match = random.randrange(0,len(self.players),1)

                validMatch = False
                #Find a valid match
                restartTimeout = 50
                timeout = 0
                while not validMatch:
                    matchName = self.players[match]
                    #You cant match with yourself or your partner
                    if matchName != playerName and matchName != self.couples[playerName]:
                        #You cant match with someone whos already got a match this round
                        if matchName not in takenPlayers:
                            #Avoid the same person getting the same match twice
                            if matchName not in self.finalMatches[playerName]:
                                validMatch = True
                                break

                    match = random.randrange(0,len(self.players),1)
                    timeout += 1
                    if timeout >= restartTimeout:
                        print_red("ERROR: No solution found. Retrying")
                        return False


                print_debug("  %s gets %s" % (playerName, matchName))
                self.finalMatches[playerName].append(matchName)
                takenPlayers.append(matchName)

        #Make sure couples didnt match with both the same people
        for player in self.couples:
            self.finalMatches[player].sort()
            self.finalMatches[self.couples[player]].sort()
            playerMatches = self.finalMatches[player]
            coupleMatches = self.finalMatches[self.couples[player]]
            if playerMatches == coupleMatches:
                print_red("ERROR: Couples cant have the same set of matches. Retrying.")
                print_red("  %s matched with %s" % (player, playerMatches))
                print_red("  %s matched with %s" % (self.couples[player], coupleMatches))
                return False

        #Make sure each person recieves expected number of gifts
        self.giftsPerPerson = dict()
        for player in self.finalMatches:
            for match in self.finalMatches[player]:
                try:
                    self.giftsPerPerson[match] += 1
                except:
                    self.giftsPerPerson[match] = 1

        for player in self.giftsPerPerson:
            if self.giftsPerPerson[player] != maxDraftRounds:
                print_red("ERROR: %s player is getting %d gifts instead of expected %d" % (player, self.giftsPerPerson[player], maxDraftRounds))
                return False

        #A valid match was found
        return True

    def sendResults(self):
        #Send email with all matches for safe keeping
        safeEmail = self.game_config.dev_email
        subject = "2024 Secret Santa Legend"
        body = "Player matches for Secret Santa:\n"
        for player in self.finalMatches:
            body += "  %s matched with %s\n" % (player, ",".join(self.finalMatches[player]))
        self.setupEmail(safeEmail, subject, body)

        #Send emails to each player with their matches
        for player in self.finalMatches:
            playerEmail = self.playerEmails[player]
            subject = "2024 Secret Santa"
            player_list = ', '.join(self.players)
            matches = " and ".join(self.finalMatches[player])
            body = (f"Dear {player},\n\nWe have decided to do a Secret Santa in place of the"
                    f" normal Christmas morning event this year. This means that each player"
                    f" ({player_list}) will be assigned {self.game_config.num_gifts} other player(s) secretly"
                    f" to get a gift for. These people should not be your significant other, so if" 
                    f" they are, please alert Will immediately.\n\nYour Secret Santa match is: {matches}!" 
                    f"\n\nPlease do not share your results with anybody else, even your partner,"
                    f" until the gift exchange!\n\nMerry Christmas All!\n\n"
                    f"Your Friendly Christmas Python Bot\n"
                    f"(This is an automated email, replies will not be received)")
            self.setupEmail(playerEmail, subject, body)

def initPlayerConfig():
    players = ['Will', 'Lauren', 'Alex']

    couples = {"Will": "Lauren",
               "Lauren": "Will",
               }

    emails = {"Will": "EMAIL@gmail.com",
              "Lauren": "EMAIL@gmail.com",
              "Alex": "EMAIL@gmail.com",
              }

    player_config = PlayerConfig(players, couples, emails)
    return player_config

def main():
    #TODO: Populate initPlayerConfig function with player data
    player_config = initPlayerConfig()

    #TODO: Fill in dev_email and dev_email_app_pass to set up the game
    num_gifts = 1
    dev_email = ""
    dev_email_app_pass = ""
    game_config = GameConfig(num_gifts=num_gifts, dev_email=dev_email, dev_email_app_pass=dev_email_app_pass)

    secretSanta = SecretSanta(player_config, game_config)
    secretSanta.solve()
    secretSanta.sendResults()

parser = argparse.ArgumentParser(description='Default.', usage="Default")
parser.add_argument('-p', action='store_true', dest='production', required=False, default=False, help='Specify whether to send final emails or not.')
parser.add_argument('-d', action='store_true', dest='debug', default=False, help='Enable debug prints.')
args = parser.parse_args()

if __name__ == "__main__":
    main()