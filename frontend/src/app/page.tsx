'use client'; // Necessário para usar hooks como useState e eventos onClick

import React, { useState, useMemo } from 'react';
import Image from 'next/image';
import { parseAnswerString, ParsedAnswer } from '../utils/parseAnswer';
import SyndromeCard from '../components/SyndromeCard';

// Interfaces
interface RetrievedChunk {
  document_id?: string | null;
  chunk_id?: string | null;
  text: string;
  score: number;
  metadata?: Record<string, any> | null;
}

interface QueryResponse {
  query: string;
  answer: string;
  retrieved_chunks: RetrievedChunk[];
  image?: {
    path: string;
    name: string;
  } | null;
}

export default function HomePage() {
  const [query, setQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'sindromes' | 'observacoes' | 'contexto'>('sindromes');

  // API Base URL
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.replace('localhost', '127.0.0.1');

  // Parse da resposta
  const parsedAnswer: ParsedAnswer | null = useMemo(() => {
    if (response?.answer) {
      return parseAnswerString(response.answer);
    }
    return null;
  }, [response]);

  // Função para consulta
  const handleQuery = async () => {
    if (!query.trim()) {
      setError('Please enter the clinical data for analysis.');
      return;
    }
    if (!apiBaseUrl) {
      setError('API configuration not found. Please contact technical support.');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    setResponse(null);

    try {
      const endpoint = `${apiBaseUrl?.replace(/\/$/, '')}/query`;
      console.log(`Sending to: ${endpoint}`);
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          query: query,
          top_k: 5,
        }),
      });

      if (!res.ok) {
        let errorBody = 'Erro desconhecido';
        try {
          errorBody = await res.text();
        } catch {}
        throw new Error(`API Error: ${res.status} - ${res.statusText}. Details: ${errorBody}`);
      }

      const data: QueryResponse = await res.json();
      setResponse(data);
      console.log('Response received:', data);
      setActiveTab('sindromes'); // Ativa a primeira aba ao receber a resposta

    } catch (err: any) {
      console.error('Error fetching data:', err);
      setError(err.message || 'Failed to connect to the API.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-4">
              <Image src="/newlogo.png" alt="LouiS" width={48} height={48} priority className="rounded-lg" />
              <h1 className="text-2xl font-bold text-gray-900">LouiS Stroke RAG</h1>
            </div>
            <nav className="hidden md:flex space-x-8">
              <a href="#" className="text-gray-600 hover:text-blue-600 font-medium">Home</a>
              <a href="#" className="text-gray-600 hover:text-blue-600 font-medium">About</a>
              <a href="https://github.com/pardinithales/final-louis" target="_blank" className="text-gray-600 hover:text-blue-600 font-medium">GitHub</a>
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Hero section */}
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">Clinical Case Analysis</h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">Enter patient clinical data and let our AI suggest vascular syndromes and neuroanatomical locations.</p>
        </div>

        {/* Clinical Analysis Section */}
        <div className="max-w-4xl mx-auto mb-12">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
            <div className="mb-6">
              <label htmlFor="queryInput" className="block text-lg font-medium text-gray-900 mb-3">
                Patient Clinical Data
              </label>
              <textarea
                id="queryInput"
                rows={6}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={isLoading}
                placeholder="Example: Patient presents right hemiparesis, expressive aphasia, conjugated gaze deviation to the left, with sudden onset symptoms..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
              />
            </div>
            <div className="flex justify-center">
              <button
                onClick={handleQuery}
                disabled={isLoading || !query.trim()}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-8 py-3 rounded-lg font-medium transition-colors"
              >
                {isLoading ? 'Processing Analysis...' : 'Analyze Case'}
              </button>
            </div>
          </div>
        </div>

        {/* Mensagem de erro */}
        {error && (
          <div className="max-w-4xl mx-auto mb-8">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <h3 className="text-red-800 font-medium">Error</h3>
              <p className="text-red-700 mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Resultados da análise */}
        {parsedAnswer && (
          <div className="max-w-6xl mx-auto">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              {/* Navigation tabs */}
              <div className="border-b border-gray-200">
                <nav className="flex space-x-8 px-8">
                  {[
                    { key: 'sindromes', label: 'Diagnoses' },
                    { key: 'observacoes', label: 'Observations' },
                    { key: 'contexto', label: 'Context' }
                  ].map(tab => (
                    <button
                      key={tab.key}
                      onClick={() => setActiveTab(tab.key as any)}
                      className={`py-4 px-1 border-b-2 font-medium text-sm ${
                        activeTab === tab.key
                          ? 'border-blue-500 text-blue-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      {tab.label}
                    </button>
                  ))}
                </nav>
              </div>

              {/* Tab content */}
              <div className="p-8">
                {/* Image display */}
                {activeTab === 'sindromes' && response?.image?.path && (
                  <div className="text-center mb-8">
                    <h4 className="text-lg font-medium text-gray-900 mb-4">Neuroanatomical Diagram</h4>
                    <div className="inline-block bg-gray-50 rounded-lg p-4">
                      <Image
                        src={`${apiBaseUrl?.replace('/api/v1', '').replace(/\/$/, '')}/${response.image.path}`}
                        alt={response.image.name || 'Stroke diagram'}
                        width={400}
                        height={300}
                        className="rounded-lg"
                      />
                    </div>
                  </div>
                )}

                {/* Diagnoses */}
                {activeTab === 'sindromes' && (
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-6">Diagnostic Hypotheses</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      {parsedAnswer.syndromes.map((syndrome, index) => (
                        <SyndromeCard 
                          key={`${syndrome.syndrome}-${index}`} 
                          syndrome={syndrome} 
                          rank={index + 1} 
                        />
                      ))}
                    </div>
                  </div>
                )}

                {/* Observations */}
                {activeTab === 'observacoes' && parsedAnswer.notes && (
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-6">Clinical Observations</h3>
                    <div className="bg-blue-50 rounded-lg p-6">
                      <p className="text-gray-800 whitespace-pre-wrap">{parsedAnswer.notes}</p>
                    </div>
                  </div>
                )}

                {/* Context */}
                {activeTab === 'contexto' && response?.retrieved_chunks && (
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-6">Reference Context</h3>
                    <div className="space-y-4">
                      {response.retrieved_chunks.map((chunk, index) => (
                        <div key={chunk.chunk_id || `chunk-${index}`} className="bg-gray-50 rounded-lg p-4">
                          <div className="flex justify-between items-center mb-2">
                            <span className="text-sm font-medium text-gray-700">
                              {chunk.metadata?.filename || chunk.metadata?.source || 'Document'}
                            </span>
                            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                              Score: {chunk.score.toFixed(2)}
                            </span>
                          </div>
                          <p className="text-gray-700 text-sm">{chunk.text}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
      

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-8 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-lg font-medium mb-2">LouiS Stroke RAG</p>
          <p className="text-gray-400 mb-4">AI-Powered Neurological Analysis System</p>
          <p className="text-sm text-gray-500">
            &copy; {new Date().getFullYear()} LouiS Stroke RAG. Developed to assist in neurovascular syndrome diagnosis.
          </p>
        </div>
      </footer>
    </div>
  );
} 