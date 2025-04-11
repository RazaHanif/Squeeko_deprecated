import React from 'react'
import { useState, useEffect, useCallback } from 'react'
import { useSpeechRecognition } from '../hooks/useSpeechRecognition'
import { summarizeText, chatWithSummary } from '../services/app'
import { SafeAreaView } from 'react-native-safe-area-context'
import { View } from 'react-native-web'

const MainScreen = () => {
    const { isListening, transcript, error: speechError, startListening, stopListening } = useSpeechRecognition()
    const [ summary, setSummary ] = useState('')
    const [ isLoading, setIsLoading ] = useState(false)
    const [ apiError, setApiError ] = useState('')
    const [ chatInput, setChatInput ] = useState('')
    const [ chatHistory, setChatHistory ] = useState([]) 

    // Get Summary when Transcription finishes
    // Only trigger when isListening changes
    useEffect( () => {
        // Trigger Summary when listening stops AND there is a transcript
        if (!isListening && transcript) {
            handleSummarization()
        }
    }, [isListening])

    const handleSummarization = useCallback( async () => {
        if (!transcript) {
            return
        }

        console.log('Start Summarization')
        setIsLoading(true)
        setApiError('')
        setSummary('')
        setChatHistory([])
        
        try {
            const result = await summarizeText(transcript)
            setSummary(result.summary)
            console.log('Summary Received')            
        } catch (err) {
            setApiError('Failed to get Summary. Please Try Again!')
            console.error('Summarization API Error', err)
        } finally {
            setIsLoading(false)
        }
    }, [transcript])


    // Handle Chat
    const handleSendChat = async () => {
        if ( !chatInput.trim() || !summary || isLoading ) {
            return
        }

        const userMessage = chatInput.trim()
        setChatInput('')
        setChatHistory( prev => [...prev, { 
            type: 'user',
            text: userMessage
        }])
        setIsLoading(true)
        setApiError('')

        try {
            const result = await chatWithSummary( summary, userMessage )
            setChatHistory( prev => [...prev, {
                type: 'llm',
                text: result.response
            }])
            console.log('Chat response received')
        } catch (err) {
            setApiError('Failed to get chat response.')
            console.error('Chat API error:', err);
            // Remove user messages if api fails
            // setChatHistory( prev => prev.slice(0, -1))
        } finally {
            setIsLoading(false)
        }
    }


    // Render UI
    return (
        <SafeAreaView style = { styles.safeArea }>
            <View style = { styles.container }>
                <Text style = { styles.title }>Squeeko</Text>

                {/* Recording Section */}
                <View style = { styles.section }>
                    <Button
                        title = { isListening ? 'Stop Recording' : 'Start Recording' }
                        onPress = { isListening ? stopListening : startListening }
                        disabled = { isLoading }
                    />
                    { isListening && <Text style = { styles.status }>Listening...</Text> }
                    { speechError && <Text style = { styles.error }>Speech Error: { speechError }</Text> }
                </View>

                {/* Transcript Display */}
                <ScrollView style = { styles.transcriptBox }>
                    <Text style = { styles.label }>Live Transcript</Text>
                    <Text>
                        { transcript || ( isListening ? '...' : 'Press Start Recording' ) }
                    </Text>
                </ScrollView>

                {/* Summary Section */}
                <View style = { styles.section }>
                    <Text style = { style.label }>Summary:</Text>
                    { isLoading && !summary && <ActivityIndicator size = 'small' /> }
                    { summary && <Text style = { styles.summaryText }>{summary}</Text> }
                    { apiError && !summary && <Text style = { styles.summaryText }>{summary}</Text> }
                </View>


            </View>
        </SafeAreaView>
    )
}