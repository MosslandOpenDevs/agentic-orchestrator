import React, { useState, useEffect, useSearchParams } from 'react';

interface Message {
  id: string;
  sender: string;
  recipient: string;
  content: string;
  timestamp: string;
}

interface MessageLogProps {
  messages: Message[];
  onFilterChange: (filter: string) => void;
  onSearchChange: (searchTerm: string) => void;
}

const MessageLog: React.FC<MessageLogProps> = ({
  messages,
  onFilterChange,
  onSearchChange,
} ) => {
  const [filter, setFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    setLoading(true);
    try {
      // Simulate fetching messages (replace with actual API call)
      const fetchedMessages: Message[] = [
        { id: '1', sender: 'Agent A', recipient: 'Agent B', content: 'Hello', timestamp: '2024-01-01T10:00:00Z' },
        { id: '2', sender: 'Agent B', recipient: 'Agent A', content: 'Response received', timestamp: '2024-01-01T10:01:00Z' },
        { id: '3', sender: 'Agent A', recipient: 'Agent C', content: 'Query about DRAIAN', timestamp: '2024-01-01T10:02:00Z' },
        { id: '4', sender: 'Agent C', recipient: 'Agent A', content: 'DRAIAN is problematic', timestamp: '2024-01-01T10:03:00Z' },
      ];
      setMessages(fetchedMessages);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleFilterChange = (newFilter: string) => {
    setFilter(newFilter);
    onFilterChange(newFilter);
  };

  const handleSearchChange = (newSearchTerm: string) => {
    setSearchTerm(newSearchTerm);
    onSearchChange(newSearchTerm);
  };

  const filteredMessages = messages.filter((message) => {
    const contentMatch = message.content.toLowerCase().includes(searchTerm.toLowerCase());
    const senderMatch = message.sender.toLowerCase().includes(searchTerm.toLowerCase());
    const recipientMatch = message.recipient.toLowerCase().includes(searchTerm.toLowerCase());
    return contentMatch || senderMatch || recipientMatch;
  });

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error.message}</div>;
  }

  return (
    <div className="max-w-screen-md mx-auto p-4">
      <div className="mb-4 flex items-center justify-between">
        <label className="mr-2 text-sm font-medium">Filter by:</label>
        <input
          type="text"
          className="rounded-md text-sm border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Enter filter term"
          value={filter}
          onChange={(e) => handleFilterChange(e.target.value)}
          aria-label="Filter messages"
        />
      </div>

      <div className="mb-4 flex items-center justify-between">
        <label className="mr-2 text-sm font-medium">Search:</label>
        <input
          type="text"
          className="rounded-md text-sm border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Search messages"
          value={searchTerm}
          onChange={(e) => handleSearchChange(e.target.value)}
          aria-label="Search messages"
        />
      </div>

      <ul className="list-disc list-inside text-sm">
        {filteredMessages.map((message) => (
          <li
            key={message.id}
            className="mb-2 p-2 rounded-md border border-gray-300"
            aria-label={`Message from ${message.sender} to ${message.recipient}`}
          >
            <strong>{message.sender}:</strong> {message.recipient} - {message.content} - {message.timestamp}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default MessageLog;