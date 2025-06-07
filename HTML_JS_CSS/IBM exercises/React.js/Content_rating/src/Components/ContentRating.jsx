import React, { Component } from 'react';
import './ContentRating.css';

class ContentRating extends Component {
  constructor() {
    super();
    this.state = {
      likes: 0,
      dislikes: 0
    };

    // Bind the methods if you're not using arrow functions
    this.handleLike = this.handleLike.bind(this);
    this.handleDislike = this.handleDislike.bind(this);
  }

  handleLike() {
    this.setState((prevState) => ({
      likes: prevState.likes + 1
    }));
  }

  handleDislike() {
    this.setState((prevState) => ({
      dislikes: prevState.dislikes + 1
    }));
  }

  render() {
    return (
      <>
        <div className='content-rating'>
          <p>
            This is a short article about the benefits of daily meditation. Feel free to rate it!
          </p>
          <div className='rating-buttons'>
            <button className="like-button" onClick={this.handleLike}>
              Like ({this.state.likes})
            </button>
            <button className="dislike-button" onClick={this.handleDislike}>
              Dislike ({this.state.dislikes})
            </button>
          </div>
        </div>
      </>
    );
  }
}

export default ContentRating;
