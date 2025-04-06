import React, { useState, useRef, useEffect } from 'react';
import {
    Box,
    TextField,
    IconButton,
    Paper,
    Typography,
    Container,
    List,
    ListItem,
    Divider,
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import ReactMarkdown from 'react-markdown';
import axios from 'axios';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    sources?: Array<{
        content: string;
        metadata: {
            title?: string;
            source?: string;
        };
    }>;
}

export const Chat: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<null | HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMessage: Message = { role: 'user', content: input };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const response = await axios.post('http://localhost:8000/api/chat', {
                message: input,
                conversation_history: messages,
            });

            const assistantMessage: Message = {
                role: 'assistant',
                content: response.data.response,
                sources: response.data.sources,
            };

            setMessages(prev => [...prev, assistantMessage]);
        } catch (error) {
            console.error('Error sending message:', error);
            const errorMessage: Message = {
                role: 'assistant',
                content: 'Sorry, I encountered an error processing your request.',
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Container maxWidth="md" sx={{ height: '100vh', py: 2 }}>
            <Paper elevation={3} sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
                    <List>
                        {messages.map((message, index) => (
                            <React.Fragment key={index}>
                                <ListItem
                                    sx={{
                                        flexDirection: 'column',
                                        alignItems: message.role === 'user' ? 'flex-end' : 'flex-start',
                                        mb: 2,
                                    }}
                                >
                                    <Paper
                                        elevation={1}
                                        sx={{
                                            p: 2,
                                            backgroundColor: message.role === 'user' ? '#e3f2fd' : '#f5f5f5',
                                            maxWidth: '80%',
                                        }}
                                    >
                                        <ReactMarkdown>{message.content}</ReactMarkdown>
                                        {message.sources && (
                                            <Box sx={{ mt: 1, borderTop: 1, borderColor: 'divider', pt: 1 }}>
                                                <Typography variant="caption" color="text.secondary">
                                                    Sources:
                                                </Typography>
                                                {message.sources.map((source, idx) => (
                                                    <Typography
                                                        key={idx}
                                                        variant="caption"
                                                        display="block"
                                                        color="text.secondary"
                                                    >
                                                        {source.metadata.title || source.metadata.source}
                                                    </Typography>
                                                ))}
                                            </Box>
                                        )}
                                    </Paper>
                                </ListItem>
                                {index < messages.length - 1 && <Divider />}
                            </React.Fragment>
                        ))}
                        <div ref={messagesEndRef} />
                    </List>
                </Box>
                <Box sx={{ p: 2, backgroundColor: 'background.default' }}>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                        <TextField
                            fullWidth
                            variant="outlined"
                            placeholder="Type your message..."
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                            disabled={isLoading}
                        />
                        <IconButton
                            color="primary"
                            onClick={handleSend}
                            disabled={isLoading}
                            sx={{ p: '10px' }}
                        >
                            <SendIcon />
                        </IconButton>
                    </Box>
                </Box>
            </Paper>
        </Container>
    );
}; 