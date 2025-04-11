import { useState, useEffect, useCallback } from 'react'
import Voice from '@react-native-voice/voice'
import { PermissionsAndroid, Platform } from 'react-native'

export const useSpeechRecognition = () => {
    const [ isListening, setIsListening ] = useState(false)
    const [ transcript, setTranscript ] = useState('')
    const [ error, setError ] = useState('')

    const requestAudioPermission = async () => {
        
        // Get user permission on android
        const requestAudioPermission = async () => { }
    }
}