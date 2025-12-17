// WebRTC Call Room Manager - Mesh Networking
console.log('✅ webrtc.js loaded');

class CallManager {
    constructor(ws, username) {
        this.ws = ws;
        this.username = username;
        this.peerConnections = {};  // Map of username -> RTCPeerConnection
        this.localStream = null;
        this.remoteStreams = {};  // Map of username -> MediaStream
        this.isInCall = false;
        this.isMuted = false;
        this.isVideoOff = false;
        this.currentCallType = null; // 'audio' or 'video'
        this.currentCallRoom = null;  // Current call room slug

        // ICE servers (STUN/TURN)
        this.iceServers = {
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' },
                { urls: 'stun:stun1.l.google.com:19302' }
            ]
        };
    }

    // Join a call room
    async joinCallRoom(callRoomSlug, callType = 'video') {
        try {
            console.log(`Joining call room: ${callRoomSlug}`);
            this.currentCallType = callType;
            this.currentCallRoom = callRoomSlug;

            // Get local media stream
            const constraints = {
                audio: true,
                video: callType === 'video'
            };

            this.localStream = await navigator.mediaDevices.getUserMedia(constraints);

            // Show call UI
            this.showCallUI(callRoomSlug);

            // Display local video
            const localVideo = document.getElementById('local-video');
            if (localVideo) {
                localVideo.srcObject = this.localStream;
            }

            this.isInCall = true;

            // Notify server that we joined
            this.sendSignal('call-room-join', {
                callRoom: callRoomSlug,
                username: this.username,
                callType: callType
            });

        } catch (error) {
            console.error('Error joining call room:', error);
            alert('Kon geen toegang krijgen tot camera/microfoon: ' + error.message);
            this.leaveCallRoom();
        }
    }

    // Handle existing participants when joining a call room
    async handleExistingParticipants(data) {
        const participants = data.participants || [];
        console.log('Existing participants received:', participants);
        console.log('My username:', this.username);

        // Create peer connections for all existing participants
        // They will send us offers, we don't send offers to them
        for (const peerUsername of participants) {
            if (peerUsername !== this.username) {
                console.log(`Creating peer connection for existing participant: ${peerUsername}`);
                await this.createPeerConnection(peerUsername);
            }
        }

        console.log('Total peer connections:', Object.keys(this.peerConnections).length);
        this.updateParticipantsCount();
    }

    // Handle new peer joining the call room
    async handlePeerJoined(data) {
        const peerUsername = data.username;

        if (peerUsername === this.username) {
            console.log('Ignoring peer-joined for myself');
            return;
        }

        console.log(`New peer joined: ${peerUsername}`);

        // Create peer connection for this peer
        await this.createPeerConnection(peerUsername);

        console.log(`Sending offer to: ${peerUsername}`);
        // Create and send offer
        const offer = await this.peerConnections[peerUsername].createOffer();
        await this.peerConnections[peerUsername].setLocalDescription(offer);

        this.sendSignal('call-offer', {
            to: peerUsername,
            from: this.username,
            callRoom: this.currentCallRoom,
            offer: offer
        });
    }

    // Handle call offer from peer
    async handleCallOffer(data) {
        const peerUsername = data.from;

        if (peerUsername === this.username) {
            return;
        }

        console.log(`Received offer from: ${peerUsername}`);

        // Create peer connection if not exists
        if (!this.peerConnections[peerUsername]) {
            await this.createPeerConnection(peerUsername);
        }

        // Set remote description
        await this.peerConnections[peerUsername].setRemoteDescription(new RTCSessionDescription(data.offer));

        // Create answer
        const answer = await this.peerConnections[peerUsername].createAnswer();
        await this.peerConnections[peerUsername].setLocalDescription(answer);

        // Send answer
        this.sendSignal('call-answer', {
            to: peerUsername,
            from: this.username,
            callRoom: this.currentCallRoom,
            answer: answer
        });
    }

    // Handle call answer from peer
    async handleCallAnswer(data) {
        const peerUsername = data.from;

        console.log(`Received answer from: ${peerUsername}`);

        if (this.peerConnections[peerUsername]) {
            await this.peerConnections[peerUsername].setRemoteDescription(new RTCSessionDescription(data.answer));
        }
    }

    // Handle ICE candidate
    async handleIceCandidate(data) {
        const peerUsername = data.from;

        if (this.peerConnections[peerUsername]) {
            try {
                await this.peerConnections[peerUsername].addIceCandidate(new RTCIceCandidate(data.candidate));
            } catch (error) {
                console.error('Error handling ICE candidate:', error);
            }
        }
    }

    // Handle peer leaving
    handlePeerLeft(data) {
        const peerUsername = data.username;
        console.log(`Peer left: ${peerUsername}`);

        // Close and remove peer connection
        if (this.peerConnections[peerUsername]) {
            this.peerConnections[peerUsername].close();
            delete this.peerConnections[peerUsername];
        }

        // Remove remote stream
        if (this.remoteStreams[peerUsername]) {
            delete this.remoteStreams[peerUsername];
        }

        // Remove video element
        const videoWrapper = document.getElementById(`remote-video-wrapper-${peerUsername}`);
        if (videoWrapper) {
            videoWrapper.remove();
        }

        // Update participants count
        this.updateParticipantsCount();
    }

    // Create RTCPeerConnection for a specific peer
    async createPeerConnection(peerUsername) {
        const pc = new RTCPeerConnection(this.iceServers);

        // Add local tracks
        if (this.localStream) {
            this.localStream.getTracks().forEach(track => {
                pc.addTrack(track, this.localStream);
            });
        }

        // Handle ICE candidates
        pc.onicecandidate = (event) => {
            if (event.candidate) {
                this.sendSignal('ice-candidate', {
                    to: peerUsername,
                    from: this.username,
                    callRoom: this.currentCallRoom,
                    candidate: event.candidate
                });
            }
        };

        // Handle remote stream
        pc.ontrack = (event) => {
            console.log(`Received track from ${peerUsername}`);

            if (event.streams[0]) {
                this.remoteStreams[peerUsername] = event.streams[0];
                this.addRemoteVideo(peerUsername, event.streams[0]);
            }
        };

        // Handle connection state changes
        pc.onconnectionstatechange = () => {
            console.log(`Connection state with ${peerUsername}:`, pc.connectionState);

            if (pc.connectionState === 'disconnected' || pc.connectionState === 'failed') {
                this.handlePeerLeft({ username: peerUsername });
            }
        };

        this.peerConnections[peerUsername] = pc;
        return pc;
    }

    // Add remote video element
    addRemoteVideo(peerUsername, stream) {
        let videoContainer = document.getElementById('remote-videos-grid');
        if (!videoContainer) {
            console.error('remote-videos-grid not found');
            return;
        }

        // Remove existing video if any
        const existingWrapper = document.getElementById(`remote-video-wrapper-${peerUsername}`);
        if (existingWrapper) {
            existingWrapper.remove();
        }

        // Create video element
        const videoWrapper = document.createElement('div');
        videoWrapper.className = 'bg-gray-900 rounded-lg overflow-hidden aspect-video relative';
        videoWrapper.id = `remote-video-wrapper-${peerUsername}`;

        const video = document.createElement('video');
        video.id = `remote-video-${peerUsername}`;
        video.autoplay = true;
        video.playsinline = true;
        video.className = 'w-full h-full object-cover';
        video.srcObject = stream;

        const label = document.createElement('div');
        label.className = 'absolute bottom-2 left-2 bg-black bg-opacity-50 px-2 py-1 rounded text-xs text-white';
        label.textContent = peerUsername;

        videoWrapper.appendChild(video);
        videoWrapper.appendChild(label);
        videoContainer.appendChild(videoWrapper);

        // Update participants count
        this.updateParticipantsCount();
    }

    // Update participants count display
    updateParticipantsCount() {
        const count = Object.keys(this.peerConnections).length + 1; // +1 for self
        console.log('Updating participants count:', count, 'peers:', Object.keys(this.peerConnections));
        const countElement = document.getElementById('participants-count');
        if (countElement) {
            countElement.textContent = `${count} ${count === 1 ? 'deelnemer' : 'deelnemers'}`;
        }
    }

    // Send signaling message via WebSocket
    sendSignal(type, data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: type,
                ...data
            }));
        }
    }

    // Toggle mute
    toggleMute() {
        if (this.localStream) {
            const audioTrack = this.localStream.getAudioTracks()[0];
            if (audioTrack) {
                audioTrack.enabled = !audioTrack.enabled;
                this.isMuted = !audioTrack.enabled;
                return this.isMuted;
            }
        }
        return false;
    }

    // Toggle video
    toggleVideo() {
        if (this.localStream) {
            const videoTrack = this.localStream.getVideoTracks()[0];
            if (videoTrack) {
                videoTrack.enabled = !videoTrack.enabled;
                this.isVideoOff = !videoTrack.enabled;
                return this.isVideoOff;
            }
        }
        return false;
    }

    // Leave call room
    leaveCallRoom() {
        console.log('Leaving call room');

        // Notify server
        if (this.currentCallRoom) {
            this.sendSignal('call-room-leave', {
                callRoom: this.currentCallRoom,
                username: this.username
            });
        }

        // Stop all tracks
        if (this.localStream) {
            this.localStream.getTracks().forEach(track => track.stop());
            this.localStream = null;
        }

        // Close all peer connections
        Object.values(this.peerConnections).forEach(pc => pc.close());
        this.peerConnections = {};
        this.remoteStreams = {};

        // Hide call UI
        this.hideCallUI();

        this.isInCall = false;
        this.currentCallRoom = null;
    }

    // Show call UI
    showCallUI(callRoomName) {
        const callModal = document.getElementById('call-modal');
        const callRoomNameEl = document.getElementById('call-room-name');
        const callStatus = document.getElementById('call-status');

        if (callModal) {
            callModal.classList.remove('hidden');
            if (callRoomNameEl) {
                callRoomNameEl.textContent = callRoomName;
            }
            if (callStatus) {
                callStatus.textContent = 'Verbonden';
                callStatus.className = 'text-green-400';
            }
        }

        // Reset participants count
        this.updateParticipantsCount();
    }

    // Hide call UI
    hideCallUI() {
        const callModal = document.getElementById('call-modal');
        if (callModal) {
            callModal.classList.add('hidden');
        }

        // Clear all video elements
        const localVideo = document.getElementById('local-video');
        if (localVideo) localVideo.srcObject = null;

        const remoteContainer = document.getElementById('remote-videos-grid');
        if (remoteContainer) {
            remoteContainer.innerHTML = '';
        }
    }
}
