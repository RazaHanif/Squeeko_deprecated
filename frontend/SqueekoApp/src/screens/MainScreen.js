import React from 'react'
import { useState, useEffect, useCallback } from 'react'
import { useSpeechRecognition } from '../hooks/useSpeechRecognition'
import { summarizeText, chatWithSummary } from '../services/app'
import { SafeAreaView } from 'react-native-safe-area-context'
import { ActivityIndicator, View } from 'react-native-web'
import { FlatList } from 'react-native-gesture-handler'


// Literally no idea why i did this
// Need to remake it but with the correct theme / design

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
                    { summary && <Text style = { styles.summaryText }>{ summary }</Text> }
                    { apiError && !summary && <Text style = { styles.error }>{ apiError }</Text> }
                </View>

                {/* Chat Section */}
                { summary && ( // Only show chat if summary exists 
                    <View style = { styles.chatContainer }>
                        <Text style = { styles.label }>Chat with Summary:</Text>
                        <FlatList
                            style = { styles.chatHistory }
                            data = { chatHistory }
                            keyExtractor = { ( _, index ) => index.toString() }
                            renderItem = { ({ item }) => (
                                <View style = { item.type === 'user' ? styles.userMessage : styles.llmMessage }>
                                    <Text style = { styles.messageText }>{ item.text }</Text>
                                </View>
                            )}
                        />
                        <View style = { styles.chatInputContainer }>
                            <TextInput 
                                style = { styles.chatInput }
                                placeholder = 'Ask about the summary...'
                                value = { chatInput }
                                onChangeText = { setChatInput }
                                editable = { !isLoading }
                            />
                            <Button 
                                title = 'Send'
                                onPress = { handleSendChat }
                                disabled = { isLoading || !chatInput.trim() }
                            />
                        </View>
                        { isLoading && chatInput && <ActivityIndicator size = 'small' /> }
                        { apiError && chatInput && <Text style = { styles.error }>{ apiError }</Text> } 
                    </View>
                )}

            </View>
        </SafeAreaView>
    )
}

const styles = StyleSheet.create({
    safeArea: {
        flex: 1,
        backgroundColor: '#f5f5f5'
    },
    container: {
        flex: 1,
        padding: 15,
    },
    title: {
        fontSize: 24,
        fontWeight: 'bold',
        marginBottom: 15,
        textAlign: 'center',
    },
    section: {
        marginBottom: 20,
        padding: 10,
        backgroundColor: '#fff',
        broderRadius: 8,
        shadowColor: '#000',
        shadowOffset: {
            width: 0,
            hegiht: 1
        },
        shadowOpacity: 0.1,
        shadowRadius: 2,
        elevation: 2,
    },
    label: {
        fontSize: 15,
        fontWeight: '600',
        marginBottom: 5,
    },
    status: {
        marginTop: 10,
        fontStyle: 'italic',
        textAlign: 'center',
        color: 'green',
    },
    error: {
        marginTop: 10,
        color: 'red',
        textAlign: 'center',
    },
    transcriptBox: {
        maxHeight: 150, // Limit height and make scrollable
        padding: 10,
        backgroundColor: '#fff',
        borderRadius: 8,
        marginBottom: 20,
        borderWidth: 1,
        borderColor: '#eee',
    },
    summaryText: {
        fontSize: 14,
        lineHeight: 20,
    },
    chatContainer: {
        flex: 1, // Take remaining space
        marginTop: 10,
    },
    chatHistory: {
        flex: 1, // Allow history to grow
        marginBottom: 10,
        borderWidth: 1,
        borderColor: '#eee',
        borderRadius: 8,
        padding: 10,
        backgroundColor: '#fff',
    },
    chatInputContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        borderTopWidth: 1,
        borderColor: '#eee',
        paddingTop: 10,
    },
    chatInput: {
        flex: 1,
        borderWidth: 1,
        borderColor: '#ccc',
        borderRadius: 20,
        paddingHorizontal: 15,
        paddingVertical: 8,
        marginRight: 10,
        backgroundColor: '#fff',
    },
    userMessage: {
        alignSelf: 'flex-end',
        backgroundColor: '#DCF8C6', // Light green
        padding: 8,
        borderRadius: 10,
        marginBottom: 5,
        maxWidth: '80%',
    },
    llmMessage: {
        alignSelf: 'flex-start',
        backgroundColor: '#E5E5EA', // Light gray
        padding: 8,
        borderRadius: 10,
        marginBottom: 5,
        maxWidth: '80%',
    },
    messageText: {
        fontSize: 14,
    },
})

export default MainScreen