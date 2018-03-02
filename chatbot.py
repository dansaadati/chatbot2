#!/usr/bin/env python
# -*- coding: utf-8 -*-

# PA6, CS124, Stanford, Winter 2018
# v.1.0.2
# Original Python code by Ignacio Cases (@cases)
######################################################################
import csv
import math
import numpy as np
import heapq
import re
from movielens import ratings
from random import randint
from deps.PorterStemmer import PorterStemmer

class Chatbot:
    """Simple class to implement the chatbot for PA 6."""

    #############################################################################
    # `moviebot` is the default chatbot. Change it to your chatbot's name       #
    #############################################################################
    def __init__(self, is_turbo=False):
      self.name = 'moviebot'
      self.is_turbo = is_turbo
      self.alphanum = re.compile('[^a-zA-Z0-9]')
      self.p = PorterStemmer()
      self.read_raw_data()
      self.read_data()
      self.binarize()

      # tuple - movie number + user opinion on it
      self.currentUserRatings = []
      self.recommendationPrompt = False
      self.minimumDataPoints = 2
      self.recommendCount = 0

      self.disambiguate = False
      self.disambiguateList = []

      # very positive, very negative words
      veryPositiveList = ['good', 'great', 'love', 'amazing', 'awesome', 'cool', 'favorite', 'best', 'dope', 'masterpiece', 'ultimate', 'fave', '5/5', 'beautiful', 'glorious', 'stunning', 'excellent', 'superior', 'outstanding']
      # lemmetize
      self.veryPositive = set()
      for word in veryPositiveList:
        self.veryPositive.add(self.p.stem(word))

      veryNegativeList = ['agonizing', 'worst', 'horrible', 'awful', 'bad',  'broken',  'appalling', 'atrocious', 'depressing', 'terrible', 'disgusting', 'dreadful', 'nasty', '0', 'unpleasant', 'deplorable', 'gross', 'offensive', 'abhorrent', 'loathsome', 'abhor', 'despise', 'detest', 'loathe']
      # lemmetize
      self.veryNegative = set()
      for word in veryNegativeList:
        self.veryNegative.add(self.p.stem(word))

      # intensifier word list
      intensifierList = ['absolute', 'really', 'very', 'extremely', 'amazingly', 'bloody', 'dreadfully', 'colossally', 'especially', 'exceptionally', 'fucking', 'hella', 'incredibly', 'literally', 'insanely', 'remarkably', 'supremely', 'terrifically']
      self.intensifiers = set()
      for word in intensifierList:
        self.intensifiers.add(self.p.stem(word))


      # thresholds
      self.loveThreshold = 3.0
      self.likeThreshold = 1.0

    #############################################################################
    # 1. WARM UP REPL
    #############################################################################

    def greeting(self):
      """chatbot greeting message"""
      #############################################################################
      # TODO: Write a short greeting message                                      #
      #############################################################################

      greeting_message = 'How can I help you?'

      #############################################################################
      #                             END OF YOUR CODE                              #
      #############################################################################

      return greeting_message

    def goodbye(self):
      """chatbot goodbye message"""
      #############################################################################
      # TODO: Write a short farewell message                                      #
      #############################################################################

      goodbye_message = 'Have a nice day!'

      #############################################################################
      #                             END OF YOUR CODE                              #
      #############################################################################

      return goodbye_message


    #############################################################################
    # 2. Modules 2 and 3: extraction and transformation                         #
    #############################################################################

    def read_raw_data(self):
        title_pattern = re.compile('(.*) \d+\.txt')

        # make sure we're only getting the files we actually want
        filename = 'data/sentiment.txt'
        contents = []
        f = open(filename)
        of = open('data/stemmed.txt', 'w')
        
        for line in f:
            # make sure everything is lower case
            line = line.lower()
            pair = line.split(',')

            # stem words
            line = self.p.stem(pair[0]) + ',' + pair[1]

            # add to the document's contents
            contents.extend(line)
            if len(line) > 0:
                of.write("".join(line))
        f.close()
        of.close()
        pass

    def evaluateSentiment(self, title, line):
      posScore = 0
      negScore = 0
      # lam = 1.0
      mult = 1
      
      removed = re.sub(r'[\"](.*?)[\"]', '', line)
      if self.is_turbo == True:
        # remove year argument from end, if year is recorded
        lastWord = title.rsplit(' ', 1)[0]
        if len(lastWord) == 6 and lastWord[1:-1].isdigit():
          title = title.rsplit(' ', 1)[0]
          removed = re.sub(title, '', line)

      negation = ['no', 'not', 'none', 'never', 'hardly', 'scarcely',
        'n\'t', 'didn\'t', 'ain\'t',
       'barely', 'doesn\'t', 'isn\'t', 'wasn\'t', 'shouldn\'t',
        'couldn\'t', 'won\'t', 'can\'t', 'don\'t']
      punctuation = set(',.?!;()')

      # Lemmetize the sentence
      line = self.lemonizeLine(removed)

      # Set negation state and calculate score
      negating = False
      for word in line.split(' '):
        if word in negation:
          negating = not negating

        if word in self.veryPositive:
          if negating:
              negScore += mult * 1
          else:
            posScore += mult * 1

        if word in self.veryNegative:
          if negating:
              posScore += mult * 1
          else:
            negScore += mult * 1

        if word in self.intensifiers:
          mult += 1

        if word in self.sentiment:
          if(self.sentiment[word] == 'pos'):
            if negating:
              negScore += mult * 1
            else:
              posScore += mult * 1
          if(self.sentiment[word] == 'neg'):
            if negating:
              posScore += mult * 1
            else:
              negScore += mult * 1

        # if we see punctuation in the word, reset negation flag
        if set(word) & punctuation:
          negating = False
      

      totalScore = posScore - negScore
      if totalScore == 0:
        return 'pos', 'Yeah, ' + title + ' could have really swung either way.'
      if totalScore >= self.loveThreshold:
        return 'pos', 'Wow, you seem to a huge fan of ' + title + '! I thought it was great too.'
      elif totalScore >= self.likeThreshold:
        return 'pos', 'Yeah, ' + title + ' was a pretty solid film. My friends and I had a great time with it.'
      elif totalScore >= -1 * self.likeThreshold:
        return 'neg', 'Oh right, I wasn\'t the biggest fan of ' + title + ' either. Glad we think alike!'
      elif totalScore >= -1 * self.loveThreshold:
        return 'neg', 'You\'re darn right about that. ' + title + ' was a complete and utter trainwreck!'
      else:
        return '?', 'So, how exactly did you feel about ' + title + '?'


      # if negScore == 0:
      #   posNegRatio = posScore
      # else:
      #   posNegRatio = float(posScore) / float(negScore)
      
      # print posNegRatio

      # if posNegRatio >= lam:
      #   return 'pos'
      # else:
      #   return 'neg'

    def grabAndValidateMovieTitle(self, line):
      lineArr = line.split(' ');
      print(lineArr)
      newLine = []
      for word in lineArr:
        if(word == "I"):
          newLine.append('I')
        else:
          newLine.append(word)
      line = ' '.join(newLine)
      print(line)

      titleReg = re.compile('[\"](.*?)[\"]')
      results = re.findall(titleReg, line)

      # too many movies quoted
      if len(results) > 1:
        return -1, None
      
      # nothing in quotes
      if len(results) == 0:
        # Creative mode: find title without quotes
        titles = []
        currentGroup = ""
        line = line.split(' ')
        previousCap = len(line)
        previousCapFlag = True
        i = 0
        if len(line) == 0:
          return -2, None

        while True:
          if line[i][0].isupper():
            if previousCapFlag:
              previousCap = i
              previousCapFlag = False

          if currentGroup == "" and line[i][0].isupper():
              currentGroup = line[i]
          elif currentGroup != "":
            currentGroup = currentGroup + " " + line[i]

          if currentGroup != "":
            titles.append(currentGroup)

          if i == len(line) - 1:
            if i == previousCap:
              break
            i = previousCap
            if previousCap == len(line):
              break
            previousCapFlag = True
            currentGroup = ""
            previousCap = len(line)
          i += 1
          if i == len(line):
            break
        titles.sort(key=len, reverse=True)
        allTitlesLowerCase = []
        for i in xrange(0, len(self.titles)):
          title = self.titles[i][0].split(' ')
          if(len(title[-1]) >= 6):
            if(title[-1][0] == '(' and title[-1][5] == ')'):
              title = title[:-1]
          titleLowerCase = ' '.join(title)
          titleLowerCase = titleLowerCase.lower()
          allTitlesLowerCase.append((titleLowerCase, i))

        resultList = []

        for title in titles:
          title = title.lower()
          for entryTitle, index in allTitlesLowerCase:
            if entryTitle.find(title) == 0:
              if entryTitle.split(' ')[0] == title.split(' ')[0]:
                resultList.append((index, self.titles[index][0]))
          if len(resultList) > 0:
            break
        if len(resultList) == 1:
          return resultList[0][0], self.titles[resultList[0][0]][0]
        elif len(resultList) > 1:
          return -4, resultList
        return -2, None
      

      # one title is found in quotes
      resultList = []
      allTitlesLowerCase = []
      for i in xrange(0, len(self.titles)):
        results[0] = results[0].lower()
        if results[0] == self.titles[i][0].lower():
          return i, self.titles[i][0]
        if self.titles[i][0].lower().find(results[0]) == 0:
          if results[0].split(' ')[0] == self.titles[i][0].lower().split(' ')[0]:
            resultList.append((i, self.titles[i][0]))

      # there is one correct title found
      if len(resultList) == 1:
        return resultList[0][0], self.titles[resultList[0][0]][0]

      # ambiguous, could be more than one
      elif len(resultList) > 1:
        return -4, resultList
      
      # nothing found
      else:
        # CREATIVE MODE: spell checking
        spellcheckIndex, spellcheckResult = self.spellcheck(results[0])
        if spellcheckIndex != -1:
          return spellcheckIndex, spellcheckResult
        return -3, None # TODO: Handle ERROR

    def lemonizeLine(self, input):
      processInput = []
      for word in input.split(' '):
        processInput.append(self.p.stem(word))


      return ' '.join(processInput)

    def disambiguateLine(self, input):
      if input == "Nevermind":
        self.disambiguateList = []
        self.disambiguate = False
        return -1, None
      titleNoYearArr = []
      for index, title in self.disambiguateList:
        if input == title:
          return index, self.titles[index][0]
        titleArr = title.split(' ')
        titleNoYear = ""
        year = ""
        if titleArr[-1][0] == "(" and titleArr[-1][5] == ")":
          year = titleArr[-1][1:5]
          titleArr = titleArr[0:-1]
          titleNoYear = ' '.join(titleArr)
          titleNoYearArr.append((index, titleNoYear))
        else:
          titleNoYearArr.append((index, title))
        if(input == year):
          return index, self.titles[index][0]
        if(input == "(" + year + ")"):
          return index, self.titles[index][0]
      
      result = ""
      for index, title in titleNoYearArr:
        matchBegin = title.find(input)
        if(matchBegin >= 0):
          tempTitleArr = title.split(' ')
          for word in tempTitleArr:
            if(word == input):
              if(result == ""):
                result = index
              else:
                return -2, None

      result = ""
      matchLoc = -1
      matchTitle = ""

      for index, title in titleNoYearArr:

        if(title.find(input) >= 0):
          if(result == ""):
            result = index
            matchLoc = title.find(input)
            matchTitle = title
          else:
            if(matchLoc != title.find(input)):
              return -2, None
            else:
              title1 = matchTitle[matchLoc + len(input):]
              title2 = title[matchLoc + len(input):]
              title1Arr = title1.split(' ')
              title2Arr = title2.split(' ')
              if title1Arr[0] == title2Arr[0]:
                return -2, None

      if(result == ""): # Could not find
        return -3, None
      else:
        return result, self.titles[result][0]

    def process(self, input):
      """Takes the input string from the REPL and call delegated functions
      that
        1) extract the relevant information and
        2) transform the information into a response to the user
      """
      #############################################################################
      # TODO: Implement the extraction and transformation in this method, possibly#
      # calling other functions. Although modular code is not graded, it is       #
      # highly recommended                                                        #
      #############################################################################
      # if self.is_turbo == True:
      #   response = 'processed %s in creative mode!!' % input
      # else:
      #   response = 'processed %s in starter mode' % input

      ignoreValidation = False
      if input == "Yes" or input == "No":
        ignoreValidation = True

      title = None
      titleIndex = -6

      if self.disambiguate:
        titleIndex, title = self.disambiguateLine(input)
        if(titleIndex == -1):
          return "Okay, tell me more about the movies you've watched!"
        elif(titleIndex == -2):
          response =  "Hmm... that's not clear enough. Do you mind specifying which movie? Here is the list again:"
          for index, result in self.disambiguateList:
            response = response + "\n " + result
          return response
        elif(titleIndex == -3):
          response = "I couldn't seem to find anything with that info. Mind trying again? Here is the list again"
          for index, result in self.disambiguateList:
            response = response + "\n " + result
          return response
        else:
          ignoreValidation = True
          self.disambiguate = False
          self.disambiguateList = []

      if not ignoreValidation:
        titleIndex, title = self.grabAndValidateMovieTitle(input)
      # TODO - HANDLE ERRORS FOR TITLE RETRIEVAL
      if titleIndex == -1:
        return "Looks like you may have multiple titles there! Please respond with just one movie at a time."
      if titleIndex == -2:
        if len(self.currentUserRatings) < self.minimumDataPoints:
          return "Please tell me a bit more about movies you've seen. Remember to surround movie titles with quotation marks!"
      if titleIndex == -3:
        return "I could not seem to find that movie. Please double check that you entered a valid movie or try another!"

      if titleIndex == -4:
        # Set flag to disambigate
        response = "Hmm...I don't know what you mean exactly. I found these matches: "
        for result in title:
          response = response + "\n " + result[1]
        response = response + "\nWhich did you mean? Type in their year, name, or roman/arabic numeral (Or say Nevermind to move on!)"
        self.disambiguate = True
        self.disambiguateList = title
        return response

      if len(self.currentUserRatings) >= self.minimumDataPoints:
        if input == "No":
          response = "Okay. Tell me a bit more about movies you've watched so I can make better recommendations."
          return response
        if input == "Yes":
          response = "You might enjoy "

      # IF VALID/NO ERRORS, EVALUATE SENTIMENT
      if title != None:
        sentiment, sampleResponse = self.evaluateSentiment(title, input)
      else:
        if input != "Yes" and input != "No":
          return "Do not understand"    

      # MAP THE TITLE TO SENTIMENT
      if title != None: #Only update matrix if they input a movie
        self.currentUserRatings.append((titleIndex, 1 if sentiment == 'pos' else -1))
        self.recommendCount = 0
      if len(self.currentUserRatings) < self.minimumDataPoints and title != None:
        response = sampleResponse
        # if sentiment == 'pos':
        #   response = "Glad to hear you had good things to say about " + title + "! Tell me a bit more about other movies you've watched!"
        # else:
        #   response = "Oh, I'll keep note that you weren't really feeling " + title + ". Please tell me a bit more about another movie you've watched."
      if(len(self.currentUserRatings) == self.minimumDataPoints and not self.recommendationPrompt):
        response += "Thanks for sharing your movie preferences. I can now make a recommendation! You should consider watching " 
      elif(len(self.currentUserRatings) > self.minimumDataPoints and title != None):
        if(sentiment == 'pos'):
          response = "I'll note you felt good about " + title + "."
        else:
          response = "Oh, that's disappointing. I'll remember how you felt about " + title + "."
        return response + " Would you like a movie recommendation? (Yes/No)"

      if len(self.currentUserRatings) >= self.minimumDataPoints:
        # at this point, we can append a recommendation to the user
        if(title == None or self.recommendationPrompt == False): #If there is a title, but first time recommending to user
          self.recommendCount += 1
          response += self.recommend(self.currentUserRatings)
          response += "! "
          response += "Would you like another recommendation? (Yes/No)"
          if(self.recommendationPrompt == False):
            self.recommendationPrompt = True

      return response

    def spellcheck(self, possibleMovieTitle):
      potentialTitleWords = possibleMovieTitle.split(' ')
      for titleIndex, title in enumerate(self.titles): 
        currentTitleWordsWithYear = title[0].split(' ')
        currentTitleWordsWithoutYear = currentTitleWordsWithYear[:-1]

        if len(potentialTitleWords) != len(currentTitleWordsWithYear) and len(potentialTitleWords) != len(currentTitleWordsWithoutYear):
          continue

        movieFits = True
        for index, word in enumerate(currentTitleWordsWithoutYear):
          if self.edit_distance(word.lower(), potentialTitleWords[index]) > 2:
            movieFits = False
            break

        if movieFits:
          return titleIndex, ' '.join(currentTitleWordsWithYear)

      return -1, ''

    # LEVENSHTEIN DISTANCE ALGORITHM
    def edit_distance(self, s1, s2):
        m = len(s1) + 1
        n = len(s2) + 1

        tbl = {}
        for i in range(m):
          tbl[i,0] = i
        for j in range(n):
          tbl[0,j] = j
        for i in range(1, m):
            for j in range(1, n):
                cost = 0 if s1[i-1] == s2[j-1] else 1
                tbl[i,j] = min(tbl[i, j-1]+1, tbl[i-1, j]+1, tbl[i-1, j-1] + cost)

        return tbl[i,j]

    #############################################################################
    # 3. Movie Recommendation helper functions                                  #
    #############################################################################

    def read_data(self):
      """Reads the ratings matrix from file"""
      # This matrix has the following shape: num_movies x num_users
      # The values stored in each row i and column j is the rating for
      # movie i by user j
      self.titles, self.ratings = ratings()
      reader = csv.reader(open('data/sentiment.txt', 'rb'))
      self.sentiment = dict(reader)


    def binarize(self):
      """Modifies the ratings matrix to make all of the ratings binary"""
      self.binarizedRatings = self.ratings

      # traverse through the ratings array
      # if score = 0, bS = 0
      # if score >= 2.5, bS = 1; score < 2.5 , bS = -1

      for rowIndex in xrange(len(self.binarizedRatings)):
        for colIndex in xrange(len(self.binarizedRatings[rowIndex])):
          currentValue = self.binarizedRatings[rowIndex][colIndex]
          if currentValue == 0:
            continue
          elif currentValue >= 2.5:
            self.binarizedRatings[rowIndex][colIndex] = 1
          else:
            self.binarizedRatings[rowIndex][colIndex] = -1


    def distance(self, u, v):
      """Calculates a given distance function between vectors u and v"""
      # TODO: Implement the distance function between vectors u and v]
      # Note: you can also think of this as computing a similarity measure
      vNorm = np.linalg.norm(v)
      uNorm = np.linalg.norm(u)
      uDotV = np.dot(u, v)
      if uNorm == 0 or vNorm == 0:
        return uDotV
      else:
        return float(uDotV) / float(vNorm * uNorm)


    def recommend(self, u):
      """Generates a list of movies based on the input vector u using
      collaborative filtering"""
      # TODO: Implement a recommendation function that takes a user vector u
      # and outputs a list of movies recommended by the chatbot

      estimatedRatings = []
      ## constructs a matrix of all predicted user ratings
      print self.currentUserRatings

      for movieIndex, movieRow in enumerate(self.ratings):
        userRating = 0
        # userRating = sum of j in user prefs (s_ij dot r_xj)

        for userMoviePreferenceIndex, userRating in self.currentUserRatings:
          # never recommend a movie the user has already marked as a preference
          if userMoviePreferenceIndex == movieIndex:
            userRating = -float('inf')
            break

          userRating += np.dot(self.distance(self.binarizedRatings[movieIndex], self.binarizedRatings[userMoviePreferenceIndex]), userRating)
        estimatedRatings.append(userRating)
        

      nPreferredMovies = heapq.nlargest(self.recommendCount, enumerate(estimatedRatings), key=lambda x: x[1])
      return self.titles[nPreferredMovies[-1][0]][0]

      #maxRated = estimatedRatings.index(max(estimatedRatings))
      #return self.titles[maxRated][0] 


    #############################################################################
    # 4. Debug info                                                             #
    #############################################################################

    def debug(self, input):
      """Returns debug information as a string for the input string from the REPL"""
      # Pass the debug information that you may think is important for your
      # evaluators
      debug_info = 'debug info'
      return debug_info


    #############################################################################
    # 5. Write a description for your chatbot here!                             #
    #############################################################################
    def intro(self): #INITIALIZATION

      return """
      Your task is to implement the chatbot as detailed in the PA6 instructions.
      Remember: in the starter mode, movie names will come in quotation marks and
      expressions of sentiment will be simple!
      Write here the description for your own chatbot!
      """


    #############################################################################
    # Auxiliary methods for the chatbot.                                        #
    #                                                                           #
    # DO NOT CHANGE THE CODE BELOW!                                             #
    #                                                                           #
    #############################################################################

    def bot_name(self):
      return self.name


if __name__ == '__main__':
    Chatbot()
