import React from 'react';

const EmojiReaction = ({ emoji, count, active, onClick }) => {
  return (
    <div 
      className={`emoji-reaction ${active ? 'active' : ''}`}
      onClick={onClick}
    >
      <span className="emoji">{emoji}</span>
      <span className="count">{count}</span>
    </div>
  );
};

export default EmojiReaction; 