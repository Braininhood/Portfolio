import React, { useState, useRef, useEffect } from 'react';

const EmojiPicker = ({ onEmojiSelect, buttonText = "😀" }) => {
  const [isOpen, setIsOpen] = useState(false);
  const pickerRef = useRef(null);
  const buttonRef = useRef(null);

  useEffect(() => {
    // Initialize emoji-picker-element once mounted
    if (pickerRef.current) {
      const picker = pickerRef.current;
      
      picker.addEventListener('emoji-click', event => {
        onEmojiSelect(event.detail.unicode);
        setIsOpen(false);
      });
    }

    // Close picker when clicking outside
    const handleClickOutside = (event) => {
      if (isOpen && pickerRef.current && !pickerRef.current.contains(event.target) && 
          buttonRef.current && !buttonRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onEmojiSelect]);

  const togglePicker = () => {
    setIsOpen(!isOpen);
  };

  return (
    <div className="emoji-picker-container">
      <button 
        className="emoji-button" 
        onClick={togglePicker}
        ref={buttonRef}
        type="button"
        aria-label="Add emoji"
      >
        {buttonText}
      </button>
      <emoji-picker 
        ref={pickerRef}
        style={{ display: isOpen ? 'block' : 'none' }}
      ></emoji-picker>
    </div>
  );
};

export default EmojiPicker; 