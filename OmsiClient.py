
import select
import socket
import os
import pdb


# module that provides an interface for all client-requests to server
class OmsiClient:
    def __init__(self, gHost, gPort, gStudentEmail,gExamID):
        # Store the original host name that was entered for UI purposes.
        self.origHost = gHost
        # Make sure the hostname is the actual address.
        self.gHost = socket.gethostbyname(gHost)
        self.gPort = gPort
        self.gStudentEmail = gStudentEmail
        self.gExamID = gExamID
        self.omsiSocket = None

        try:
            self.assertSocketCanBeCreated()
        except ValueError as e:
            raise ValueError('Unable to create socket! Check Parameters', 
               self.origHost, self.gPort, e)

    def assertSocketCanBeCreated(self):
        response = self.configureSocket()
        if response:
            response.close()
            return True
        return False

    # initialization of socket, no connection is established yet
    def configureSocket(self):
        try:
            # create TCP socket (domain, type)
            pSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            pSocket.settimeout(20)
            # initiate server connection to global
            pSocket.connect((self.gHost, self.gPort))

            return pSocket

        # connection problem
        except socket.error as xxx_todo_changeme:
            # if socket was created, close socket
            (value, message) = xxx_todo_changeme.args
            # if socket was created, close socket
            if pSocket:
                pSocket.close()
            raise ValueError("Error configuring socket! " + message)
            return None


    # creates file with the questions on the client's machine
    def createExamQuestionsFile(self):

        try:

            lFilePath = 'ExamQuestions.txt'
            lNewFile = open(lFilePath, 'w')
            return lNewFile

        # something went wrong
        except IOError:
            return False
    
    # creates code file on the client's machine
    def createCodeFile(self):

        try:

            lFilePath = 'code.R'
            lNewFile = open(lFilePath, 'w')
            return lNewFile

        # something went wrong
        except IOError:
            return False

    # creates data file on the client's machine
    def createSuppFile(self):

        try:

            lFilePath = 'SuppFile'
            lNewFile = open(lFilePath, 'w')
            return lNewFile

        # something went wrong
        except IOError:
            return False

    # close the connection
    # returning success/failure message or 
    # initiating a file transfer from server to student
    # NEVER USED?
    def getResponseFromServer(pSocket):
        # block until server response received
        lServerResponse = pSocket.recv(1024)
        print("Server Response: " + lServerResponse, '\n')
        if lServerResponse != "file":
            pSocket.close()
            if lServerResponse == "s":
                return True
            else:
                print('server notifies us of fail:\n')
                print(lServerResponse)
                return False
        else:
            return 'file'


    # TODO: Update this routine
    # this opens a file with read permissions on the file
    # ATTENTION: an open file is returned! Call file.close() on the returned object
    def openFileOnClient(self, pFileName):
        try:
          lFilePath = os.path.join('', pFileName)
          lOpenFile = open(lFilePath, "r")
          print('client file opened')
          return lOpenFile
        except IOError:
            print('client file could not be opened')
            try:
                # file was not in the home directory, try to see id the file is in the code's directory
                lOpenFile = open(pFileName, "r")
                return lOpenFile
            except:
                # file was not to be found at all; 
                # the name is wrong or the file is somewhere unexpected
                print("Error: File %s could not be opened" % pFileName)
                return False


    # download exam questions from professor's machine
    def getExamQuestionsFile(self, pClientSocket):

        # filename = self.createExamQuestionsFile()
        # create local file to write exam questions to
        lExamQuestionsFile = self.createExamQuestionsFile()

        # if file was not created, notify the user
        if not lExamQuestionsFile:
            print('Error: Exam questions file not created on client\'s machine.')
            return

        # create boolean to track success
        lSuccess = False

        # if file was successfully created, notify server to 
        # begin sending exam questions
        try:
            print("requesting exam questions from server")
            pClientSocket.send("ClientWantsQuestions")

            # write data from server to file
            qfilelen = 0
            while True:
                # ready = select.select([pClientSocket], [], [], 2)
                print("Client Waiting to recv")
                lChunkOfFile = pClientSocket.recv(1024)
                if lChunkOfFile[-1] == chr(0):  # last chunk
                    lSuccess = True
                    lChunkOfFile = lChunkOfFile.rstrip(chr(0))
                qfilelen = qfilelen + len(lChunkOfFile)
                # print "Client recvd chunk {0}".format(lChunkOfFile)
                print("Client recvd Quest. File chunk; first line:\n")
                print(lChunkOfFile.split('\n')[0], '\n')
                lExamQuestionsFile.write(lChunkOfFile)
                if lSuccess: break

        finally:
            # if exam questions were not successfully downloaded, print error
            if lSuccess:
                print("Exam questions successfully read from server.")
                print(qfilelen, 'bytes in all')
            else:
                print("Error: Exam questions were not successfully read from server.")

            # close file, regardless of success
            lExamQuestionsFile.close()
            # close socket

            # return File
            return lSuccess, lExamQuestionsFile

    # download any files in files/ from professor's machine
    def getSuppFile(self, pClientSocket):

        lCodeFile = self.createSuppFile()

        # if file was not created, notify the user
        if not lCodeFile:
            print('Error: Supplementary file not created on client\'s machine.')
            return

        # create boolean to track success
        lSuccess = False

        # if file was successfully created, notify server to 
        # begin sending exam questions
        try:
            print("requesting supplementary file from server")
            pClientSocket.send("ClientWantsSuppFile")

            # write data from server to file
            qfilelen = 0
            while True:
                # ready = select.select([pClientSocket], [], [], 2)
                print("Client Waiting to recv")
                lChunkOfFile = pClientSocket.recv(1024)
                if lChunkOfFile[-1] == chr(0):  # last chunk
                    lSuccess = True
                    lChunkOfFile = lChunkOfFile.rstrip(chr(0))
                qfilelen = qfilelen + len(lChunkOfFile)
                # print "Client recvd chunk {0}".format(lChunkOfFile)
                print("Client recvd Supp. File chunk; first line:\n")
                print(lChunkOfFile.split('\n')[0], '\n')
                lCodeFile.write(lChunkOfFile)
                if lSuccess: break

        finally:
            # if exam questions were not successfully downloaded, print error
            if lSuccess:
                print("Supplementary file successfully read from server.")
                print(qfilelen, 'bytes in all')
            else:
                print("Error: Supplementary file not successfully read from server.")

            # close file, regardless of success
            lCodeFile.close()
            # close socket

            # return File
            return lSuccess, lCodeFile


    # sends a file from the client to the server
    def sendFileToServer(self, pFileName):

        # open the file -> this handles exceptions effectively
        print("Opening file " + pFileName)
        lOpenFile = self.openFileOnClient(pFileName)
        print(lOpenFile)
        v = open('VERSION')
        version = v.readline()
        while True:
           try:
               ### if not self.omsiSocket:
               ###     self.omsiSocket = self.configureSocket()
               self.omsiSocket = self.configureSocket()
               # tell the server that we are sending a file; 'OMSI0001' is
               # the signal for this;  0 bytes serve delimiter between fields
               msg = "OMSI0001" + '\0' + pFileName + "\0" + \
                  self.gStudentEmail + "\0" + version \
                  + self.gExamID
               self.omsiSocket.send(msg)
               print('notified server a file is coming,')
               print('via the message', msg)
               # send the file
               print("sending file %s" % pFileName)
               # wait for go-ahead from server
               goahead = self.omsiSocket.recv(1024)
               if goahead != 'ReadyToAcceptClientFile':
                  print('server and client out of sync')
                  print('received from server:', goahead)
                  print('closing client socket, suggest reconnect')
               while (True):
                   lFileChunk = lOpenFile.read(1024)
                   nread = len(lFileChunk)
                   if nread == 0: 
                      print('end of file')
                      break
                   print("file chunk:\n", lFileChunk)
                   self.omsiSocket.send(lFileChunk)
                   print('sent', len(lFileChunk), 'bytes')
               lOpenFile.close()
               print('file closed\n')
               lServerResponse = self.omsiSocket.recv(1024)
               return lServerResponse
               ### raise ValueError("Error sending file to server!", \
               ###   pFileName, e)
           except socket.error as e:
               print('exception')
               print("Got error {0} for {1}".format(e, pFileName))
               print("Setting socket to none, retrying")
               self.omsiSocket = None

