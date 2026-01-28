"use client";

import { useState } from "react";

interface FileWithUrl {
  file: File;
  url: string;
}

export default function AdminPage() {
  const [filesWithUrls, setFilesWithUrls] = useState<FileWithUrl[]>([]);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files).map((file) => ({
        file,
        url: "",
      }));
      setFilesWithUrls(newFiles);
    }
  };

  const handleUrlChange = (index: number, url: string) => {
    setFilesWithUrls((prev) => {
      const updated = [...prev];
      updated[index].url = url;
      return updated;
    });
  };

  const handleUpload = async () => {
    if (filesWithUrls.length === 0) {
      setMessage("Please select at least one PDF file.");
      return;
    }

    setUploading(true);
    setMessage("");

    const formData = new FormData();
    filesWithUrls.forEach(({ file, url }) => {
      formData.append("files", file);
      formData.append("urls", url || "");
    });

    try {
      const response = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setMessage(`Success! ${data.message}`);
        setFilesWithUrls([]);
        const fileInput = document.getElementById(
          "fileInput"
        ) as HTMLInputElement;
        if (fileInput) fileInput.value = "";
      } else {
        setMessage(`Error: ${data.detail || "Upload failed"}`);
      }
    } catch (error) {
      setMessage(
        `Error: ${error instanceof Error ? error.message : "Upload failed"}`
      );
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <div className="bg-white shadow-lg rounded-lg p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Admin Panel</h1>
          <p className="text-gray-600 mb-8">
            Upload PDF files for ingestion into the knowledge base
          </p>

          <div className="space-y-6">
            <div>
              <label
                htmlFor="fileInput"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Select PDF Files
              </label>
              <input
                id="fileInput"
                type="file"
                accept=".pdf"
                multiple
                onChange={handleFileChange}
                className="block w-full text-sm text-gray-500
                  file:mr-4 file:py-2 file:px-4
                  file:rounded-md file:border-0
                  file:text-sm file:font-semibold
                  file:bg-blue-50 file:text-blue-700
                  hover:file:bg-blue-100
                  cursor-pointer"
              />
            </div>

            {filesWithUrls.length > 0 && (
              <div className="bg-gray-50 rounded-md p-4">
                <h3 className="text-sm font-medium text-gray-700 mb-3">
                  Selected Files ({filesWithUrls.length}):
                </h3>
                <div className="space-y-4">
                  {filesWithUrls.map(({ file, url }, index) => (
                    <div key={index} className="space-y-2">
                      <div className="text-sm text-gray-600">
                        • {file.name} ({(file.size / 1024).toFixed(2)} KB)
                      </div>
                      <input
                        type="url"
                        placeholder="Enter source URL (optional)"
                        value={url}
                        onChange={(e) => handleUrlChange(index, e.target.value)}
                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}

            <button
              onClick={handleUpload}
              disabled={uploading || filesWithUrls.length === 0}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-md font-semibold
                hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed
                transition-colors duration-200"
            >
              {uploading ? "Processing..." : "Upload and Ingest PDFs"}
            </button>

            {message && (
              <div
                className={`p-4 rounded-md ${
                  message.startsWith("Success")
                    ? "bg-green-50 text-green-800 border border-green-200"
                    : "bg-red-50 text-red-800 border border-red-200"
                }`}
              >
                {message}
              </div>
            )}
          </div>

          <div className="mt-8 pt-6 border-t border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">
              Instructions
            </h2>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>• Select one or more PDF files to upload</li>
              <li>
                • Provide source URLs for each file to enable clickable
                citations
              </li>
              <li>
                • URLs are optional but recommended for proper source
                attribution
              </li>
              <li>
                • Files will be automatically processed and added to the
                knowledge base
              </li>
              <li>
                • After successful ingestion, temporary files will be
                automatically deleted
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
