'use client';

import React, { useEffect, useState } from 'react';
import { Legal, LegalDocument } from '@/lib/api';
import { toastManager } from '@/components/Toast';

interface DocForm {
  doc_type: string;
  title: string;
  content: string;
  content_html?: string;
  requires_acceptance: boolean;
  display_order: number;
}

export default function LegalDocsAdminPage() {
  const [loading, setLoading] = useState(false);
  const [documents, setDocuments] = useState<LegalDocument[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [selectedDoc, setSelectedDoc] = useState<LegalDocument | null>(null);
  const [showVersions, setShowVersions] = useState(false);
  const [versions, setVersions] = useState<LegalDocument[]>([]);

  const [formData, setFormData] = useState<DocForm>({
    doc_type: 'privacy_policy',
    title: '',
    content: '',
    content_html: '',
    requires_acceptance: true,
    display_order: 0,
  });

  const docTypes = [
    { code: 'privacy_policy', label: 'Privacy Policy' },
    { code: 'terms_of_service', label: 'Terms of Service' },
    { code: 'return_policy', label: 'Return Policy' },
    { code: 'warranty_policy', label: 'Warranty Policy' },
    { code: 'cookie_policy', label: 'Cookie Policy' },
  ];

  useEffect(() => {
    loadDocuments();
  }, []);

  async function loadDocuments() {
    setLoading(true);
    try {
      const docs = await Legal.listDocuments();
      setDocuments(docs);
    } catch (err) {
      console.error('Failed to load documents:', err);
      toastManager.error('Failed to load documents');
    } finally {
      setLoading(false);
    }
  }

  async function loadVersions(docType: string) {
    try {
      const vers = await Legal.getDocumentVersions(docType);
      setVersions(vers);
      setShowVersions(true);
    } catch (err) {
      console.error('Failed to load versions:', err);
      toastManager.error('Failed to load document versions');
    }
  }

  async function handleSaveDocument() {
    if (!formData.title || !formData.content) {
      toastManager.error('Please fill in title and content');
      return;
    }

    setLoading(true);
    try {
      if (editingId) {
        const updated = await Legal.updateDocument(editingId, formData);
        setDocuments(documents.map(d => d.id === editingId ? updated : d));
        toastManager.success('Document updated successfully');
      } else {
        const newDoc = await Legal.createDocument(formData);
        setDocuments([...documents, newDoc]);
        toastManager.success('Document created successfully');
      }
      setShowForm(false);
      resetForm();
    } catch (err) {
      console.error('Failed to save document:', err);
      toastManager.error('Failed to save document');
    } finally {
      setLoading(false);
    }
  }

  function startEdit(doc: LegalDocument) {
    setEditingId(doc.id);
    setFormData({
      doc_type: doc.doc_type,
      title: doc.title,
      content: doc.content,
      content_html: doc.content_html,
      requires_acceptance: doc.requires_acceptance,
      display_order: doc.display_order,
    });
    setShowForm(true);
  }

  function resetForm() {
    setEditingId(null);
    setFormData({
      doc_type: 'privacy_policy',
      title: '',
      content: '',
      content_html: '',
      requires_acceptance: true,
      display_order: 0,
    });
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Legal Documents Management</h1>

      {/* Add/Edit Form */}
      <div className="mb-8">
        <button
          onClick={() => {
            setShowForm(!showForm);
            if (!showForm) resetForm();
          }}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 mb-4"
        >
          {showForm ? 'Cancel' : 'Create New Document'}
        </button>

        {showForm && (
          <div className="p-6 bg-white rounded-lg border border-gray-200 shadow-sm">
            <h2 className="text-xl font-semibold mb-4">{editingId ? 'Edit' : 'Create New'} Document</h2>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium mb-2">Document Type</label>
                <select
                  value={formData.doc_type}
                  onChange={(e) => setFormData({ ...formData, doc_type: e.target.value })}
                  className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={editingId !== null}
                >
                  {docTypes.map(t => (
                    <option key={t.code} value={t.code}>{t.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Title</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Privacy Policy v2"
                />
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">Content (Markdown)</label>
              <textarea
                value={formData.content}
                onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                rows={10}
                placeholder="# Privacy Policy&#10;&#10;Your content here..."
              />
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">HTML Content (Optional)</label>
              <textarea
                value={formData.content_html || ''}
                onChange={(e) => setFormData({ ...formData, content_html: e.target.value })}
                className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                rows={5}
                placeholder="Rendered HTML version..."
              />
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium mb-2">Display Order</label>
                <input
                  type="number"
                  value={formData.display_order}
                  onChange={(e) => setFormData({ ...formData, display_order: parseInt(e.target.value) })}
                  className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="flex items-end">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.requires_acceptance}
                    onChange={(e) => setFormData({ ...formData, requires_acceptance: e.target.checked })}
                    className="mr-2"
                  />
                  <span className="text-sm font-medium">Requires User Acceptance</span>
                </label>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleSaveDocument}
                disabled={loading}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                {loading ? 'Saving...' : editingId ? 'Update Document' : 'Create Document'}
              </button>
              <button
                onClick={() => {
                  setShowForm(false);
                  resetForm();
                }}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Version History Modal */}
      {showVersions && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-96 overflow-y-auto">
            <h2 className="text-xl font-semibold mb-4">Version History</h2>
            <div className="space-y-2 mb-4">
              {versions.map(v => (
                <div key={v.id} className="p-3 border rounded-lg hover:bg-gray-50">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium">Version {v.version}</p>
                      <p className="text-sm text-gray-600">{new Date(v.created_at).toLocaleString()}</p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-sm ${v.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                      {v.is_active ? 'Active' : 'Previous'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
            <button
              onClick={() => setShowVersions(false)}
              className="w-full px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* Selected Document Preview */}
      {selectedDoc && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-96 overflow-y-auto">
            <h2 className="text-xl font-semibold mb-2">{selectedDoc.title}</h2>
            <p className="text-sm text-gray-600 mb-4">Version {selectedDoc.version}</p>
            <div className="prose prose-sm max-w-none mb-4">
              {selectedDoc.content_html ? (
                <div dangerouslySetInnerHTML={{ __html: selectedDoc.content_html }} />
              ) : (
                <pre className="bg-gray-100 p-3 rounded text-sm overflow-x-auto whitespace-pre-wrap">
                  {selectedDoc.content}
                </pre>
              )}
            </div>
            <button
              onClick={() => setSelectedDoc(null)}
              className="w-full px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* Documents List */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Active Documents</h2>
        {loading && documents.length === 0 ? (
          <div className="text-center py-8 text-gray-500">Loading documents...</div>
        ) : documents.length === 0 ? (
          <div className="text-center py-8 text-gray-500">No documents created yet</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {documents.map(doc => (
              <div key={doc.id} className="p-4 border rounded-lg bg-white shadow-sm hover:shadow-md transition">
                <h3 className="font-semibold text-lg mb-2">{doc.title}</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Type: <span className="font-medium">{doc.doc_type.replace(/_/g, ' ')}</span>
                </p>
                <p className="text-sm text-gray-600 mb-3">
                  Version: <span className="font-medium">{doc.version}</span>
                </p>
                <div className="flex flex-wrap gap-2 mb-3">
                  <span className={`px-2 py-1 text-xs rounded-full ${doc.requires_acceptance ? 'bg-orange-100 text-orange-800' : 'bg-gray-100 text-gray-800'}`}>
                    {doc.requires_acceptance ? 'Requires Acceptance' : 'Informational'}
                  </span>
                  <span className={`px-2 py-1 text-xs rounded-full ${doc.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                    {doc.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setSelectedDoc(doc)}
                    className="flex-1 px-3 py-2 bg-blue-100 text-blue-600 rounded hover:bg-blue-200 text-sm"
                  >
                    View
                  </button>
                  <button
                    onClick={() => startEdit(doc)}
                    className="flex-1 px-3 py-2 bg-yellow-100 text-yellow-600 rounded hover:bg-yellow-200 text-sm"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => loadVersions(doc.doc_type)}
                    className="flex-1 px-3 py-2 bg-purple-100 text-purple-600 rounded hover:bg-purple-200 text-sm"
                  >
                    History
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
