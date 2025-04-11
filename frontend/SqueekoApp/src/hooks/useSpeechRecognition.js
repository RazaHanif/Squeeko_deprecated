import { useState, useEffect, useCallback } from 'react'
import Voice from '@react-native-voice/voice'
import { PermissionsAndroid, Platform } from 'react-native'

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


}
