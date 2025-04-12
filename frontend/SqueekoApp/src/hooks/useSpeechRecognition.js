import { useState, useEffect, useCallback } from 'react'
import Voice from '@react-native-voice/voice'
import { PermissionsAndroid, Platform } from 'react-native'


/* 
This whole file IDK 
I feel like i should redo this from scratch
So i actually understand whats going on

Might just keep the Function names and redo all the logic
*/

export const useSpeechRecognition = () => {
    const [ isListening, setIsListening ] = useState(false)
    const [ transcript, setTranscript ] = useState('')
    const [ error, setError ] = useState('')

    // Get user permission on android
    const requestAudioPermission = async () => { 
        if ( Platform.OS === 'android' ) {
            try { 
                const granted = await PermissionsAndroid.request(
                    PermissionsAndroid.PERMISSIONS.RECORD_AUDIO,
                    {
                        title: 'Squeeko Audio Permission',
                        message: 'Squeeko needs access to your microphone for transcription',
                        buttonNeutral: 'Ask Me Later',
                        buttonNegative: 'Cancel',
                        buttonPositive: 'OK'
                    },
                )
                return granted === PermissionsAndroid.RESULTS.GRANTED
            } catch (err) {
                console.warn(err)
                return false
            }
        }
        // iOS permissions handled automatically when first used
        // default granted permission for iOS
        return true
    }

    const onSpeechStart = useCallback( (e) => {
        console.log('onSpeechStart:', e)
        setIsListening(true)
        setTranscript('')
        setError('')
    }, [])
    
    const onSpeechEnd = useCallback( (e) => {
        console.log('onSpeechEnd:', e)
        setIsListening(false)
    }, [])
    
    // Idk what the setTranscript thing does
    const onSpeechResults = useCallback( (e) => {
        console.log('onSpeechResults:', e)
        if (e.value && e.value.length > 0) {
            setTranscript(e.value[0])
        }
    }, [])
    
    const onSpeechError = useCallback( (e) => {
        console.log('onSpeechError:', e)
        setError(JSON.stringify(e.error))
        setIsListening(false)
    }, [])

    useEffect( () => {
        // Setup listeners
        Voice.onSpeechStart = onSpeechStart
        Voice.onSpeechEnd = onSpeechEnd
        Voice.onSpeechResults = onSpeechResults
        Voice.onSpeechError = onSpeechError

        // Unmount listeners
        return () => {
            Voice.destroy().then(Voice.removeAllListeners)
        }
    }, [onSpeechStart, onSpeechEnd, onSpeechResults, onSpeechError])

    const startListening = async () => {
        
        // Check for user permission
        const hasPermission = await requestAudioPermission()
        if (!hasPermission) {
            setError('Microphone permission denied')
            return
        }

        // Default to US English, make this change to user region & make it configerable
        try {
            await Voice.start('en-US')
            setIsListening(true)
            setTranscript('')
            setError('')
        } catch (err) {
            console.error('Error starting voice recognition', err)
            setError(JSON.stringify(err))
        }
    }

    const stopListening = async () => {
        try {
            await Voice.stop()
            setIsListening(false)
        } catch (err) {
            console.error('Error stopping voice recognition', err)
            setError(JSON.stringify(err))
        }
    }

    return {
        isListening,
        transcript,
        error,
        startListening,
        stopListening,
    }
}
