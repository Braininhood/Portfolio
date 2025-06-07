import React from 'react';
import "./TotalCost.css";

const TotalCost = ({ totalCosts, handleClick, ItemsDisplay }) => {
  return (
    <div className="pricing-app">
      <div className="display_box">
        <div className="header">
          <p className="preheading"><h3>Total cost for the event</h3></p>
          <button className="back-button" onClick={handleClick}>Back to Selection</button>
        </div>
        <div className="cost-breakdown">
          <div className="cost-section">
            <h4>Venue Cost:</h4>
            <p className="price">${totalCosts.venueCost}</p>
          </div>
          <div className="cost-section">
            <h4>AV Equipment Cost:</h4>
            <p className="price">${totalCosts.avCost}</p>
          </div>
          <div className="cost-section">
            <h4>Meals Cost:</h4>
            <p className="price">${totalCosts.mealsCost}</p>
          </div>
          <div className="total-section">
            <h3>Total Event Cost:</h3>
            <h2 id="pre_fee_cost_display" className="price">
              ${totalCosts.totalCost}
            </h2>
          </div>
        </div>
        <div className="items-list">
          <h4>Selected Items:</h4>
          <ItemsDisplay />
        </div>
      </div>
    </div>
  );
};

export default TotalCost;
