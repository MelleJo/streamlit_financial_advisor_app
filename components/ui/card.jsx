import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './card';
import { Alert, AlertDescription } from './alert';

const AdviceModule = ({ title, content, definitions }) => {
  const [copied, setCopied] = useState(false);

  const copyText = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  // Process content to highlight terms
  const processContent = (text) => {
    if (!text) return [];
    
    const parts = [];
    let currentPos = 0;
    
    // Sort definitions by length (longest first) to handle overlapping terms
    const terms = Object.keys(definitions).sort((a, b) => b.length - a.length);
    
    const regex = new RegExp(`\\b(${terms.join('|')})\\b`, 'gi');
    const matches = [...text.matchAll(regex)];
    
    matches.forEach((match) => {
      const term = match[0];
      const startPos = match.index;
      
      // Add text before the term
      if (startPos > currentPos) {
        parts.push({
          type: 'text',
          content: text.slice(currentPos, startPos)
        });
      }
      
      // Add the highlighted term
      parts.push({
        type: 'term',
        content: term,
        definition: definitions[term.toLowerCase()]
      });
      
      currentPos = startPos + term.length;
    });
    
    // Add remaining text
    if (currentPos < text.length) {
      parts.push({
        type: 'text',
        content: text.slice(currentPos)
      });
    }
    
    return parts;
  };

  const processedContent = processContent(content);

  return (
    <Card className="mb-4 bg-white shadow-sm">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-xl font-bold">{title}</CardTitle>
        <button
          onClick={copyText}
          className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 hover:bg-accent hover:text-accent-foreground h-9 px-3"
        >
          {copied ? (
            <Check className="h-4 w-4 text-green-500" />
          ) : (
            <Copy className="h-4 w-4 text-gray-500" />
          )}
          <span className="ml-2">{copied ? 'Gekopieerd!' : 'Kopieer'}</span>
        </button>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {processedContent.map((part, index) => {
            if (part.type === 'term') {
              return (
                <span
                  key={index}
                  className="inline-block bg-blue-50 text-blue-700 px-1 rounded cursor-pointer hover:bg-blue-100 transition-colors"
                  onClick={() => {
                    if (part.definition) {
                      // Show definition in an Alert
                      document.getElementById(`definition-${index}`).classList.remove('hidden');
                    }
                  }}
                >
                  {part.content}
                  {part.definition && (
                    <Alert
                      id={`definition-${index}`}
                      className="mt-2 hidden"
                    >
                      <AlertDescription>
                        {part.definition}
                      </AlertDescription>
                    </Alert>
                  )}
                </span>
              );
            }
            return <span key={index}>{part.content}</span>;
          })}
        </div>
      </CardContent>
    </Card>
  );
};

export default AdviceModule;