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
}

export default function HomePage() {
  const [query, setQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'sindromes' | 'observacoes' | 'contexto'>('sindromes');

  // API Base URL
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

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
      const endpoint = `${apiBaseUrl.replace(/\/$/, '')}/query`;
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
      <header className="bg-white shadow-sm border-b border-gray-200 mb-8">
        <div className="container-app py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Image src="/logo_louis.png" alt="LouiS logo" width={40} height={40} className="rounded-lg" />
              <h1 className="text-2xl font-bold text-gray-900">LouiS Stroke RAG</h1>
            </div>
            <div className="text-sm text-gray-600">
              <span className="font-medium">Neurological Analysis System</span>
            </div>
          </div>
        </div>
      </header>

      <main className="container-app pb-12">
        {/* Seção de consulta */}
        <section className="mb-10">
          <div className="card">
            <div className="card-header border-b">
              <h2 className="text-xl font-bold text-gray-900">Clinical Case Analysis</h2>
              <p className="text-gray-600 text-sm mt-2">
                Enter patient clinical data to identify vascular syndromes and neuroanatomical locations.
              </p>
            </div>
            <div className="card-body">
              <div className="mb-6">
                <label htmlFor="queryInput" className="block text-sm font-medium text-gray-700 mb-2">
                  Patient Clinical Data
                </label>
                <textarea
                  id="queryInput"
                  rows={5}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  disabled={isLoading}
                  placeholder="Ex: Patient presents right hemiparesis, expressive aphasia, conjugated gaze deviation to the left..."
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div className="flex justify-end">
                <button
                  onClick={handleQuery}
                  disabled={isLoading}
                  className="btn btn-primary btn-lg font-semibold"
                >
                  {isLoading ? 'Processing...' : 'Analyze Case'}
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Mensagem de erro */}
        {error && (
          <div className="mb-10 bg-red-50 border-l-4 border-red-500 p-5 rounded-md">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-base font-medium text-red-800">Error</h3>
                <p className="text-base text-red-700 mt-2">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Resultados da análise */}
        {parsedAnswer && (
          <section className="mb-10">
            <div className="card overflow-hidden">
              {/* Abas de navegação */}
              <div className="border-b border-gray-200">
                <div className="tab-nav">
                  <button
                    onClick={() => setActiveTab('sindromes')}
                    className={`tab-button ${activeTab === 'sindromes' ? 'tab-button-active' : 'tab-button-inactive'}`}
                  >
                    Diagnoses
                  </button>
                  <button
                    onClick={() => setActiveTab('observacoes')}
                    className={`tab-button ${activeTab === 'observacoes' ? 'tab-button-active' : 'tab-button-inactive'}`}
                  >
                    Observations
                  </button>
                  <button
                    onClick={() => setActiveTab('contexto')}
                    className={`tab-button ${activeTab === 'contexto' ? 'tab-button-active' : 'tab-button-inactive'}`}
                  >
                    Context
                  </button>
                </div>
              </div>

              {/* Conteúdo da aba selecionada */}
              <div className="p-8">
                {/* Diagnósticos */}
                {activeTab === 'sindromes' && (
                  <div>
                    <h3 className="text-xl font-semibold mb-8">Main Diagnostic Hypotheses (Syndromes)</h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
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

                {/* Observações */}
                {activeTab === 'observacoes' && parsedAnswer.notes && (
                  <div>
                    <h3 className="text-xl font-semibold mb-6">Observations and Additional Analysis</h3>
                    <div className="bg-blue-50 rounded-lg p-6 prose">
                      <p className="whitespace-pre-wrap text-base">{parsedAnswer.notes}</p>
                    </div>
                  </div>
                )}

                {/* Contexto */}
                {activeTab === 'contexto' && response?.retrieved_chunks && (
                  <div>
                    <h3 className="text-xl font-semibold mb-6">Context Used in Analysis</h3>
                    <div className="space-y-6">
                      {response.retrieved_chunks.map((chunk, index) => (
                        <div key={chunk.chunk_id || `chunk-${index}`} className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
                          <div className="bg-gray-50 px-6 py-3 border-b border-gray-200 flex justify-between items-center">
                            <div className="text-sm font-medium text-gray-700">
                              {chunk.metadata?.filename || chunk.metadata?.source || 'Document'}
                            </div>
                            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                              Score: {chunk.score.toFixed(2)}
                            </span>
                          </div>
                          <div className="p-6">
                            <p className="text-base text-gray-700 leading-relaxed">{chunk.text}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </section>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-8 mt-12">
        <div className="container-app">
          <div className="text-center text-sm text-gray-600">
            <p>© {new Date().getFullYear()} LouiS Stroke RAG - Neurological Analysis System</p>
            <p className="mt-2">Developed to assist in the diagnosis of neurovascular syndromes</p>
          </div>
        </div>
      </footer>
    </div>
  );
} 