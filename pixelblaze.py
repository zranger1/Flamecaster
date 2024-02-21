#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
 A lightweight version of the pixelblaze-client python library. with only the functionality
 needed for this Artnet proxy project.

"""

# ----------------------------------------------------------------------------
# Copyright 2020-2022 by the pixelblaze-client team
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons
# to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
# BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# ----------------------------------------------------------------------------

import errno
import json
import logging
import socket
import traceback
from enum import Flag, IntEnum
from typing import Union

import websocket

from ArtnetUtils import clamp


# --- MAIN CLASS
# noinspection PyBroadException
class Pixelblaze:
    """
    The Pixelblaze class presents a simple synchronous interface to a single Pixelblaze's websocket API.

    This is a lightweight version of the pixelblaze-client python library, with only the functionality
    needed for this Artnet proxy project.
    """
    # --- PRIVATE DATA
    default_recv_timeout = 1
    max_open_retries = 5
    ws = None
    connected = False
    ipAddress = None

    # Pattern cache
    cacheRefreshTime = 0
    cacheRefreshInterval = 1000  # milliseconds used internally
    patternCache = None

    # Parser state cache
    latestStats = None
    latestSequencer = None
    latestPreview = None
    latestConfig = None
    connectionBroken = False

    # --- OBJECT LIFETIME MANAGEMENT (CREATION/DELETION)

    def __init__(self, ipAddress: str):
        """Initializes an object for communicating with and controlling a Pixelblaze.

           Doesn't require the Pixelblaze to be active or connected at the time of creation.
           If the initial open fails, the object will try to reconnect when used.

        Args:
            ipAddress (str): The Pixelblaze's IPv4 address in the usual dotted-quads numeric format
             (for example, "192.168.4.1").
        """
        self.ipAddress = ipAddress
        self.setCacheRefreshTime(600)  # seconds used in public api

        # try to open the connection, but trap any exception if it fails unless
        # ignoreOpenFailure is True
        try:
            self.open()
        except Exception:
            pass

    def __enter__(self):
        """Internal class method for resource management.

        Returns:
            Pixelblaze: This object.
        """
        return self

    def __exit__(self, exc_type, exc_value, tb):
        """Internal class method for resource management.

        Args:
            exc_type (_type_): As per Python standard.
            exc_value (_type_): As per Python standard.
            tb (_type_): As per Python standard.
        """
        # Make sure we clean up after ourselves.
        if self is not None:
            self.close()

    # --- CONNECTION MANAGEMENT

    def is_connected(self) -> bool:
        """Returns True if the Pixelblaze is connected, False otherwise."""
        return self.connected

    def open(self):
        """
        Opens a websocket connection to the Pixelblaze.  
        
        This is called automatically when a Pixelblaze object is created; it is not necessary to explicitly 
        call open to connect unless the websocket has been explicitly closed by the user previously.
        """
        if self.connected is False:
            uri = "ws://" + self.ipAddress + ":81"
            retryCount = 0
            while True:
                try:
                    self.ws = websocket.create_connection(uri, sockopt=(
                        (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1), (socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),))
                    break
                except websocket._exceptions.WebSocketConnectionClosedException:
                    # print("Open failed.  Retry # ",retryCount)
                    retryCount += 1
                    if retryCount >= self.max_open_retries:
                        raise

            self.ws.settimeout(self.default_recv_timeout)
            self.connected = True

            # Reset our caches so we'll get them afresh.
            self.latestStats = None
            self.latestConfig = None
            self.latestSequencer = None

            self.requestConfigSettings()
            self.setSendPreviewFrames(False)

    def close(self):
        """Close websocket connection."""
        if self.connected is True:
            self.ws.close()
            self.connected = False

    # --- LOW-LEVEL SEND/RECEIVE

    class MessageTypes(IntEnum):
        """Types of binary messages sent and received by a Pixelblaze.  The first byte of a binary
          frame contains the message type.
        """
        putSourceCode = 1  # from client to PB
        putByteCode = 3  # from client to PB
        previewImage = 4  # from client to PB
        previewFrame = 5  # from PB to client
        getSourceCode = 6  # from PB to client
        getProgramList = 7  # from client to PB
        putPixelMap = 8  # from client to PB
        ExpanderConfig = 9  # from client to PB *and* PB to client
        # SPECIAL MESSAGE TYPES: These aren't part of the Pixelblaze protocol; they're flags for the state machine.
        specialConfig = -1
        specialStats = -2

    class FrameTypes(Flag):
        """Continuation flags for messages sent and received by a Pixelblaze.
           The second byte of a binary frame tells whether this packet is part of a set.
        """
        frameNone = 0
        frameFirst = 1
        frameMiddle = 2
        frameLast = 4

    def wsReceive(self, *, binaryMessageType: MessageTypes = None) -> Union[str, bytes, None]:
        """Wait for a message of a particular type from the Pixelblaze.

        Args:
            binaryMessageType (messageTypes, optional): The type of binary message to wait for (if None,
            waits for a text message). Defaults to None.

        Returns:
            Union[str, bytes, None]: The message received from the Pixelblaze (of type bytes for
            binaryMessageTypes, otherwise of type str), or None if a timeout occurred.
        """
        message = None

        try:
            frame = self.ws.recv()
            if type(frame) is str:
                # Some frames are sent unrequested and often interrupt the conversation; we'll just
                # save the most recent one and retrieve it later when we want it.
                if frame.startswith('{"fps":'):
                    self.latestStats = frame
                    if binaryMessageType is self.MessageTypes.specialStats:
                        return frame
                elif frame.startswith('{"activeProgram":'):
                    self.latestSequencer = frame
                    if binaryMessageType is self.MessageTypes.specialConfig:
                        return frame
                elif frame.startswith('{"name":'):
                    self.latestConfig = frame
                    if binaryMessageType is self.MessageTypes.specialConfig:
                        return frame
                # We wanted a text frame, we got a text frame.
                elif binaryMessageType is None:
                    return frame
            else:
                frameType = frame[0]
                if frameType == self.MessageTypes.previewFrame.value:
                    self.latestPreview = frame[1:]
                    # This packet type doesn't have frameType flags.
                    if binaryMessageType == self.MessageTypes.previewFrame:
                        return frame[1:]

                # Check the flags to see if we need to read more packets.
                frameFlags = frame[1]
                if message is None and not (frameFlags & self.FrameTypes.frameFirst.value):
                    raise  # The first frame must be a start frame
                if message is not None and (frameFlags & self.FrameTypes.frameFirst.value):
                    raise  # We shouldn't get a start frame after we've started
                if message is None:
                    message = frame[2:]  # Start with the first packet...
                else:
                    message += frame[2:]  # ...and append the rest until we reach the end.

                # If we've received all the packets, deal with the message.
                if frameFlags & self.FrameTypes.frameLast.value:
                    # Expander config frames are ONLY sent during a config request, but they sometimes arrive
                    # out of order, so we'll save them and retrieve them separately.
                    if frameType == self.MessageTypes.ExpanderConfig:
                        if binaryMessageType == self.MessageTypes.specialConfig:
                            return message
                    return message

        except websocket._exceptions.WebSocketTimeoutException:  # timeout -- we can just ignore this
            return None

        except websocket._exceptions.WebSocketConnectionClosedException:  # try reopening
            print("wsReceive - socket closed on device " + self.ipAddress)
            self.connectionBroken = True
            self.close()
            self.open()

        except IOError as e:
            # add test for WinError 10054 - existing connection reset
            if e.errno == errno.EPIPE or e.errno == 10054:
                print("wsReceive - socket reset on device " + self.ipAddress)
                self.connectionBroken = True
                self.close()
                self.open()

        except Exception as e:
            self.connectionBroken = True
            traceback.print_stack()
            logging.debug(f"wsReceive: unknown exception: {e}")
            raise

    def sendPing(self):
        """Send a Ping message to the Pixelblaze and wait for the Acknowledgement response.

        Returns:
            Union[str, None]: The acknowledgement message received from the Pixelblaze, or None if a timeout occurred.
        """
        return self.wsSendJson({"ping": True})

    def maintain_connection(self):
        """
        Flush receive buffer and see that connection handshake is maintained.

        It keeps the receive buffer clear of stray packets, and since connection maintenance
        is handled by ws.recv(), keeps the connection alive.  Otherwise, it'll time out and hang or
        disconnect after about 10 minutes.

        Will run until there are no more packets to be read if loop is True, otherwise it will
        read only the first available packet.

        """
        try:
            self.wsReceive(binaryMessageType=None)

        except Exception as e:
            self.connectionBroken = True
            logging.debug("Super Exceptional Exception in connection maintenance for " + self.ipAddress)
            logging.debug(e)
            raise

    def wsSendString(self, command: str):
        """Send a command with a preformatted string as data, and don't wait around for a response.
        (but still do all the connection maintenance stuff)

        Args:
            command str: string

        """
        try:
            self.ws.send(command)

        except websocket._exceptions.WebSocketConnectionClosedException:
            # print("wsSendString received WebSocketConnectionClosedException")
            self.close()
            self.open()  # try reopening

        except IOError as e:
            # print("wsSendString received IOError")
            # add test for WinError 10054 - existing connection reset
            if e.errno == errno.EPIPE or e.errno == 10054:
                self.close()
                self.open()

        except Exception as e:
            logging.debug("wsSendString received unexpected exception " + str(e))
            self.close()
            self.open()

    def wsSendJson(self, command: dict, *, expectedResponse=None) -> Union[str, bytes, None]:
        """Send a JSON-formatted command to the Pixelblaze, and optionally wait for a suitable response.

        Args:
            command (dict): A Python dictionary which will be sent to the Pixelblaze as a JSON command.
            expectedResponse (str, optional): If present, the initial key of the expected JSON response
            to the command. Defaults to None.

        Returns:
            Union[str, bytes, None]: The message received from the Pixelblaze (of type bytes for binaryMessageTypes,
            otherwise of type str), or None if a timeout occurred.
        """
        self.connectionBroken = False
        while True:
            try:
                self.open()  # make sure it's open, even if it closed while we were doing other things.
                self.ws.send(json.dumps(command, indent=None, separators=(',', ':')).encode("utf-8"))

                if expectedResponse is None:
                    return None

                    # If the pipe broke while we were sending, restart from the beginning.
                if self.connectionBroken:
                    break

                # Wait for the expected response.
                while True:
                    # Loop until we get the right text response.
                    if type(expectedResponse) is str:
                        if expectedResponse == "activeProgram":
                            response = self.wsReceive(binaryMessageType=self.MessageTypes.specialConfig)
                        else:
                            response = self.wsReceive(binaryMessageType=None)
                        if response is None:
                            break
                        if response.startswith(f'{{"{expectedResponse}":'):
                            break
                    # Or the right binary response.
                    elif type(expectedResponse) is self.MessageTypes:
                        response = self.wsReceive(binaryMessageType=expectedResponse)
                        break
                # Now that we've got the right response, return it.
                return response

            except websocket._exceptions.WebSocketConnectionClosedException:
                self.connectionBroken = True
                self.close()
                self.open()  # try reopening

            except IOError as e:
                # add test for WinError 10054 - existing connection reset
                if e.errno == errno.EPIPE or e.errno == 10054:
                    self.connectionBroken = True
                    self.close()
                    self.open()

            except Exception:
                self.connectionBroken = True
                self.close()
                self.open()  # try reopening  # raise

    def wsSendBinary(self, binaryMessageType: MessageTypes, blob: bytes, *, expectedResponse: str = None):
        """Send a binary command to the Pixelblaze, and optionally wait for a suitable response.

        Args:
            binaryMessageType (messageTypes, optional): The type of binary message to send.
            blob (bytes): The message body to be sent.
            expectedResponse (str, optional): If present, the initial key of the expected JSON response to
            the command. Defaults to None.

        Returns:
            response: The message received from the Pixelblaze (of type bytes for binaryMessageTypes,
            otherwise of type str), or None if a timeout occurred.
        """
        self.connectionBroken = False
        while True:
            try:
                # Break the frame into manageable chunks.
                response = None
                maxFrameSize = 8192
                if binaryMessageType == self.MessageTypes.putByteCode:
                    maxFrameSize = 1280
                for i in range(0, len(blob), maxFrameSize):

                    # Set the frame header values.
                    frameHeader = bytearray(2)
                    frameHeader[0] = binaryMessageType.value
                    frameFlag = self.FrameTypes.frameNone
                    if i == 0:
                        frameFlag |= self.FrameTypes.frameFirst
                    if (len(blob) - i) <= maxFrameSize:
                        frameFlag |= self.FrameTypes.frameLast
                    else:
                        frameFlag = self.FrameTypes.frameMiddle

                    # noinspection PyTypeChecker
                    frameHeader[1] = frameFlag.value

                    # Send the packet.
                    self.ws.send_binary(bytes(frameHeader) + blob[i:i + maxFrameSize])

                    # If the pipe broke while we were sending, restart from the beginning.
                    if self.connectionBroken:
                        break

                    # Wait for the expected response.
                    while True:
                        # Loop until we get the right text response.
                        if type(expectedResponse) is str:
                            response = self.wsReceive(binaryMessageType=None)
                            if response is None:
                                break
                            if response.startswith(expectedResponse):
                                break
                        # Or the right binary response.
                        elif type(expectedResponse) is self.MessageTypes:
                            response = self.wsReceive(binaryMessageType=expectedResponse)
                            break
                # Now that we've sent all the chunks, return the last status received.
                return response

            except websocket._exceptions.WebSocketConnectionClosedException:
                # print("wsSendBinary reconnection")
                # try reopening
                self.connectionBroken = True
                self.close()
                self.open()

            except IOError as e:
                # add test for WinError 10054 - existing connection reset
                if e.errno == errno.EPIPE or e.errno == 10054:
                    self.connectionBroken = True
                    self.close()
                    self.open()

            except Exception:
                # print("wsSendBinary received unexpected exception")
                # try reopening
                self.connectionBroken = True
                self.close()
                self.open()  # raise

    def getPeers(self):
        """A new command, added to the API but not yet implemented as of v2.29/v3.24, that will return
         a list of all the Pixelblazes visible on the local network segment.

        Returns:
            TBD: To be defined once @wizard implements the function.
        """
        self.wsSendJson({"getPeers": True})
        return self.wsReceive(binaryMessageType=None)

    def setSendPreviewFrames(self, doUpdates: bool):
        """Set whether the Pixelblaze sends pattern preview frames.

        Args:
            doUpdates (bool): True sends preview frames, False stops.
        """
        self.wsSendJson({"sendUpdates": doUpdates})

    def getPreviewFrame(self) -> bytes:
        return self.latestPreview

    # --- PATTERNS tab: SEQUENCER section

    class SequencerModes(IntEnum):
        Off = 0
        ShuffleAll = 1
        Playlist = 2

    def setSequencerMode(self, sequencerMode: SequencerModes, *, saveToFlash: bool = False):
        """Sets the sequencer mode to one of the available sequencerModes (Off, ShuffleAll, or Playlist).

        Args:
            sequencerMode (enum): The desired sequencer mode.
            saveToFlash (bool, optional): If True, the setting is stored in Flash memory;
            otherwise the value reverts on a reboot. Defaults to False.
        """
        self.wsSendJson({"sequencerMode": sequencerMode, "save": saveToFlash}, expectedResponse=None)

    def setSequencerState(self, sequencerState: bool):
        """Set the run state of the sequencer.

        Args:
            sequencerState (bool): A boolean value determining whether the sequencer should run.
            reverts on a reboot. Defaults to False.
        """
        self.wsSendJson({"runSequencer": sequencerState})

    def getActiveVariables(self) -> dict:
        """Gets the names and values of all variables exported by the current pattern.

        Returns:
            dict: A dictionary containing all the variables exported by the active pattern, with variableName
            as the key and variableValue as the value.
        """
        return json.loads(self.wsSendJson({"getVars": True}, expectedResponse="vars")).get('vars')

    def setActiveVariables(self, dictVariables: dict):
        """Sets the values of one or more variables exported by the current pattern.

        Variables not present in the current pattern are ignored.

        Args:
            dictVariables: A dictionary containing the variables to be set, with variableName as the key
            and variableValue as the value.
        """
        self.wsSendJson({"setVars": dictVariables})

    # --- PATTERNS tab: SAVED PATTERNS section: convenience functions
    def requestConfigSequencer(self):
        """Retrieves the Sequencer state when the Pixelblaze gets around to it
        """
        self.requestConfigSettings()

    def getActivePattern(self) -> str:
        """Returns the ID of the pattern currently running on the Pixelblaze.

        Returns:
            str: The patternId of the current pattern, if any; otherwise an empty string.
        """
        return self.latestSequencer.get('activeProgram').get('activeProgramId', "")

    def sendPatternToRenderer(self, bytecode: bytes, controls=None):
        """Sends a blob of bytecode and a JSON dictionary of UI controls to the Renderer.
           Mimics the actions of the webUI code editor.

        Args:
            bytecode (bytes): A valid blob of bytecode as generated by the Editor tab in the Pixelblaze webUI.
            controls (dict, optional): a dictionary of UI controls exported by the pattern, with controlName as
            the key and controlValue as the value. Defaults to {}.
        """
        if controls is None:
            controls = {}
        self.wsSendJson({"pause": True, "setCode": {"size": len(bytecode)}}, expectedResponse="ack")
        self.wsSendBinary(self.MessageTypes.putByteCode, bytecode, expectedResponse="ack")
        self.wsSendJson({"setControls": controls}, expectedResponse="ack")
        self.wsSendJson({"pause": False}, expectedResponse="ack")

    # --- SETTINGS menu

    def requestConfigSettings(self):
        self.wsSendJson({"getConfig": True})

    def getPixelCount(self) -> Union[int, None]:
        """Returns the number of LEDs connected to the Pixelblaze.

        Returns:
            int: The number of LEDs connected to the Pixelblaze.
        """
        return self.latestConfig.get('pixelCount', None)

    def pauseRenderer(self, doPause: bool):
        """Pause rendering. Lasts until unpause() is called or the Pixelblaze is reset.

        CAUTION: For advanced users only.  Only used to stop the render engine before
        sending new bytecode.

        If you don't know exactly why you want to do this, DON'T DO IT.

        Args:
            doPause (bool): If True, pause the render engine; if False, resume it.
        """
        self.wsSendJson({"pause": doPause}, expectedResponse="ack")

    def setCacheRefreshTime(self, seconds: int):
        """Set the interval, in seconds, after which calls to `getPatternList()` clear the pattern cache
           and fetch a new pattern list from the Pixelblaze.

        The Default is 600 seconds (10 minutes); the maximum allowable value is
        clamped to a million seconds (about 277 hours, or 11.5 days).

        Args:
            seconds (int): The maximum age of the pattern cache.
        """
        self.cacheRefreshInterval = 1000 * clamp(seconds, 0, 1000000)
