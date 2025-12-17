// End-to-End Encryption using Web Crypto API
console.log('✅ crypto.js loaded');

class E2ECrypto {
    constructor() {
        this.keyPair = null;
        this.publicKeyString = null;
        this.privateKey = null;
    }

    // Generate RSA-OAEP key pair
    async generateKeyPair() {
        try {
            this.keyPair = await window.crypto.subtle.generateKey(
                {
                    name: "RSA-OAEP",
                    modulusLength: 2048,
                    publicExponent: new Uint8Array([1, 0, 1]),
                    hash: "SHA-256"
                },
                true, // extractable
                ["encrypt", "decrypt"]
            );

            // Export public key to string for storage
            const publicKeyBuffer = await window.crypto.subtle.exportKey("spki", this.keyPair.publicKey);
            this.publicKeyString = this.arrayBufferToBase64(publicKeyBuffer);

            // Store private key in localStorage (encrypted in production!)
            const privateKeyBuffer = await window.crypto.subtle.exportKey("pkcs8", this.keyPair.privateKey);
            const privateKeyBase64 = this.arrayBufferToBase64(privateKeyBuffer);
            localStorage.setItem('e2e_private_key', privateKeyBase64);

            this.privateKey = this.keyPair.privateKey;

            return this.publicKeyString;
        } catch (error) {
            console.error('Error generating key pair:', error);
            throw error;
        }
    }

    // Load existing private key from localStorage
    async loadPrivateKey() {
        const privateKeyBase64 = localStorage.getItem('e2e_private_key');
        if (!privateKeyBase64) {
            return false;
        }

        try {
            const privateKeyBuffer = this.base64ToArrayBuffer(privateKeyBase64);
            this.privateKey = await window.crypto.subtle.importKey(
                "pkcs8",
                privateKeyBuffer,
                {
                    name: "RSA-OAEP",
                    hash: "SHA-256"
                },
                true,
                ["decrypt"]
            );
            return true;
        } catch (error) {
            console.error('Error loading private key:', error);
            return false;
        }
    }

    // Import public key from string
    async importPublicKey(publicKeyString) {
        try {
            const publicKeyBuffer = this.base64ToArrayBuffer(publicKeyString);
            return await window.crypto.subtle.importKey(
                "spki",
                publicKeyBuffer,
                {
                    name: "RSA-OAEP",
                    hash: "SHA-256"
                },
                true,
                ["encrypt"]
            );
        } catch (error) {
            console.error('Error importing public key:', error);
            throw error;
        }
    }

    // Hybrid Encryption: Encrypt message with AES-GCM, then encrypt AES key with RSA
    async encryptMessage(message, recipientPublicKey) {
        try {
            // 1. Generate random AES-GCM key
            const aesKey = await window.crypto.subtle.generateKey(
                {
                    name: "AES-GCM",
                    length: 256
                },
                true,
                ["encrypt", "decrypt"]
            );

            // 2. Generate random IV for AES-GCM
            const iv = window.crypto.getRandomValues(new Uint8Array(12));

            // 3. Encrypt message with AES-GCM
            const encoder = new TextEncoder();
            const messageData = encoder.encode(message);

            const encryptedMessage = await window.crypto.subtle.encrypt(
                {
                    name: "AES-GCM",
                    iv: iv
                },
                aesKey,
                messageData
            );

            // 4. Export AES key
            const aesKeyData = await window.crypto.subtle.exportKey("raw", aesKey);

            // 5. Encrypt AES key with recipient's RSA public key
            const publicKey = await this.importPublicKey(recipientPublicKey);
            const encryptedAesKey = await window.crypto.subtle.encrypt(
                {
                    name: "RSA-OAEP"
                },
                publicKey,
                aesKeyData
            );

            // 6. Return encrypted package
            return {
                encryptedKey: this.arrayBufferToBase64(encryptedAesKey),
                encryptedContent: this.arrayBufferToBase64(encryptedMessage),
                iv: this.arrayBufferToBase64(iv)
            };
        } catch (error) {
            console.error('Error encrypting message:', error);
            throw error;
        }
    }

    // Hybrid Decryption: Decrypt AES key with RSA, then decrypt message with AES
    async decryptMessage(encryptedPackage) {
        if (!this.privateKey) {
            throw new Error('Private key not loaded');
        }

        try {
            // Handle both old format (string) and new format (object)
            if (typeof encryptedPackage === 'string') {
                // Old RSA-only format - try to decrypt
                const encryptedBuffer = this.base64ToArrayBuffer(encryptedPackage);
                const decryptedBuffer = await window.crypto.subtle.decrypt(
                    {
                        name: "RSA-OAEP"
                    },
                    this.privateKey,
                    encryptedBuffer
                );
                const decoder = new TextDecoder();
                return decoder.decode(decryptedBuffer);
            }

            // New hybrid format
            const { encryptedKey, encryptedContent, iv } = encryptedPackage;

            // 1. Decrypt AES key with RSA private key
            const encryptedAesKeyBuffer = this.base64ToArrayBuffer(encryptedKey);
            const aesKeyData = await window.crypto.subtle.decrypt(
                {
                    name: "RSA-OAEP"
                },
                this.privateKey,
                encryptedAesKeyBuffer
            );

            // 2. Import AES key
            const aesKey = await window.crypto.subtle.importKey(
                "raw",
                aesKeyData,
                {
                    name: "AES-GCM"
                },
                false,
                ["decrypt"]
            );

            // 3. Decrypt message with AES-GCM
            const encryptedContentBuffer = this.base64ToArrayBuffer(encryptedContent);
            const ivBuffer = this.base64ToArrayBuffer(iv);

            const decryptedMessage = await window.crypto.subtle.decrypt(
                {
                    name: "AES-GCM",
                    iv: ivBuffer
                },
                aesKey,
                encryptedContentBuffer
            );

            const decoder = new TextDecoder();
            return decoder.decode(decryptedMessage);
        } catch (error) {
            console.error('Error decrypting message:', error);
            return '[🔒 Kan bericht niet ontsleutelen]';
        }
    }

    // Helper: ArrayBuffer to Base64
    arrayBufferToBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return window.btoa(binary);
    }

    // Helper: Base64 to ArrayBuffer
    base64ToArrayBuffer(base64) {
        const binary = window.atob(base64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
        }
        return bytes.buffer;
    }

    // Check if user has keys
    hasKeys() {
        return localStorage.getItem('e2e_private_key') !== null;
    }

    // Clear all keys (for logout)
    clearKeys() {
        localStorage.removeItem('e2e_private_key');
        this.keyPair = null;
        this.publicKeyString = null;
        this.privateKey = null;
    }
}
