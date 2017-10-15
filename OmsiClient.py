
import select
import socket
import os
import pdb


# module that provides an interface for all client-requests to server
class OmsiClient:
    def __init__(self, gHost, gPort, gStudentEmail):
        # Store the original host name that was entered for UI purposes.
        self.origHost = gHost
        # Make sure the hostname is the actual address.
        self.gHost = socket.gethostbyname(gHost)
        self.gPort = gPort
        self.gStudentEmail = gStudentEmail
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
            # initiate server connection to global
            pSocket.connect((self.gHost, self.gPort))

            return pSocket

        # connection problem
        except socket.error, (value, message):
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


    # close the connection
    # returning success/failure message or 
    # initiating a file transfer from server to student
    # NEVER USED?
    def getResponseFromServer(pSocket):
        # block until server response received
        lServerResponse = pSocket.recv(1024)
        print "Server Response: " + lServerResponse, '\n'
        if lServerResponse != "file":
            pSocket.close()
            if lServerResponse == "s":
                return True
            else:
                print 'server notifies us of fail:\n'
                print lServerResponse
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
          return lOpenFile
        except IOError:
            try:
                # file was not in the home directory, try to see id the file is in the code's directory
                lOpenFile = open(pFileName, "r")
                return lOpenFile
            except:
                # file was not to be found at all; 
                # the name is wrong or the file is somewhere unexpected
                print "Error: File %s could not be opened" % pFileName
                return False


    # download exam questions from professor's machine
    def getExamQuestionsFile(self, pClientSocket):

        # filename = self.createExamQuestionsFile()
        # create local file to write exam questions to
        lExamQuestionsFile = self.createExamQuestionsFile()

        # if file was not created, notify the user
        if not lExamQuestionsFile:
            print 'Error: Exam questions file not created on client\'s machine.'
            return

        # create boolean to track success
        lSuccess = False

        # if file was successfully created, notify server to 
        # begin sending exam questions
        try:
            print "Requesting exam questions from server."
            pClientSocket.send("ClientWantsQuestions")

            # write data from server to file
            while True:
                # ready = select.select([pClientSocket], [], [], 2)
                print "Client Waiting to recv"
                lChunkOfFile = pClientSocket.recv(1024)
                if lChunkOfFile[-1] == chr(0):  # last chunk
                    lSuccess = True
                    lChunkOfFile = lChunkOfFile.rstrip(chr(0))
                # print "Client recvd chunk {0}".format(lChunkOfFile)
                print "Client recvd Quest. File chunk; first line:\n"
                print lChunkOfFile.split('\n')[0], '\n'
                lExamQuestionsFile.write(lChunkOfFile)
                if lSuccess: break

        finally:
            # if exam questions were not successfully downloaded, print error
            if lSuccess:
                print "Exam questions successfully read from server."
            else:
                print "Error: Exam questions were not successfully read from server."

            # close file, regardless of success
            lExamQuestionsFile.close()
            # close socket

            # return File
            return lSuccess, lExamQuestionsFile


    # sends a file from the client to the server
    def sendFileToServer(self, pFileName):

        # open the file -> this handles exceptions effectively
        print "Opening file " + pFileName
        lOpenFile = self.openFileOnClient(pFileName)

        try:
            ldebugging = lOpenFile.read(1024)
            lOpenFile.seek(0)
            lCanIReadFromFile = True
        except:
            lCanIReadFromFile = False

        # if file is ready to be sent, connect to the server
        if not lCanIReadFromFile:
            return "cannot read input file"

        try:
            if not self.omsiSocket:
                self.omsiSocket = self.configureSocket()

            # tell the server that we are sending a file; 'OMSI0001' is
            # the signal for this;  0 bytes serve delimiter between fields
            msg = "OMSI0001" + pFileName + "\0" + self.gStudentEmail + "\0"
            self.omsiSocket.send(msg)
            print 'notified server a file is coming'

            # send the file
            print "sending file %s" % pFileName
            print 'first chunk'
            lFileChunk = lOpenFile.read(1024)
            lFileChunk = lFileChunk
            while (True):
                print "file chunk:\n", lFileChunk
                self.omsiSocket.send(lFileChunk)
                print 'sent', len(lFileChunk), 'bytes'
                print 'next chunk, if any'
                lFileChunk = lOpenFile.read(1024)
                nread = len(lFileChunk)
                if nread == 0: 
                   print 'end of file'
                   break
                print 'read', len(lFileChunk), 'bytes'

            lOpenFile.close()
            print 'file closed\n'

            lServerResponse = self.omsiSocket.recv(1024)
            print 'server response:', lServerResponse

            return lServerResponse
        except ValueError as e:
            raise ValueError("Error sending file to server!", pFileName, e)
        except socket.error as e:
            print "Got error {0} for {1}.\nSetting socket to none and retrying...".format(e, pFileName)
            self.omsiSocket = None
            self.sendFileToServer(pFileName)








