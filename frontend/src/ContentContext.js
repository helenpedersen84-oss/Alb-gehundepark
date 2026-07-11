import React, { createContext, useContext, useEffect, useState } from 'react';
import { CONTENT } from './mock';
import api from './api';

const ContentContext = createContext(null);

// Merge live content (hero/about/contact) over the static CONTENT defaults.
function mergeContent(live) {
  if (!live) return CONTENT;
  return {
    ...CONTENT,
    hero: { ...CONTENT.hero, ...(live.hero || {}) },
    about: { ...CONTENT.about, ...(live.about || {}) },
    contact: { ...CONTENT.contact, ...(live.contact || {}) },
  };
}

export function ContentProvider({ children }) {
  const [content, setContent] = useState(CONTENT);

  useEffect(() => {
    api.getContent().then((live) => setContent(mergeContent(live))).catch(() => {});
  }, []);

  return <ContentContext.Provider value={content}>{children}</ContentContext.Provider>;
}

export function useContent() {
  return useContext(ContentContext) || CONTENT;
}
