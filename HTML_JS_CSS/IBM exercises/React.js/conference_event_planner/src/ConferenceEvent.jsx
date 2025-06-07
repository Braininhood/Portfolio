import React, { useState } from "react";
import "./ConferenceEvent.css";
import TotalCost from "./TotalCost";
import { useSelector, useDispatch } from "react-redux";
import { incrementQuantity, decrementQuantity } from "./venueSlice";
import { incrementAvQuantity, decrementAvQuantity } from "./avSlice";
import { toggleMealSelection, setAttendees } from "./mealsSlice";

const ConferenceEvent = () => {
    const [showItems, setShowItems] = useState(false);
    const [numberOfPeople, setNumberOfPeople] = useState(1);
    const venueItems = useSelector((state) => state.venue);
    const avItems = useSelector((state) => state.av);
    const mealItems = useSelector((state) => state.meals);
    const dispatch = useDispatch();
    const remainingAuditoriumQuantity = 3 - venueItems.find(item => item.name === "Auditorium Hall (Capacity:200)").quantity;

    const handleToggleItems = () => {
        console.log("handleToggleItems called");
        setShowItems(!showItems);
    };

    const handleAddToCart = (index) => {
        if (venueItems[index].name === "Auditorium Hall (Capacity:200)" && venueItems[index].quantity >= 3) {
          return; 
        }
        dispatch(incrementQuantity(index));
    };
    
    const handleRemoveFromCart = (index) => {
        if (venueItems[index].quantity > 0) {
          dispatch(decrementQuantity(index));
        }
    };

    const handleIncrementAvQuantity = (index) => {
        dispatch(incrementAvQuantity(index));
    };

    const handleDecrementAvQuantity = (index) => {
        dispatch(decrementAvQuantity(index));
    };

    const handleMealSelection = (index) => {
        dispatch(toggleMealSelection(index));
    };

    const handleAttendeeChange = (index, value) => {
        const count = parseInt(value) || 0;
        dispatch(setAttendees({ index, count }));
    };

    const getItemsFromTotalCost = () => {
        const items = [];
        // Add venue items
        venueItems.forEach(item => {
            if (item.quantity > 0) {
                items.push({
                    name: item.name,
                    quantity: item.quantity,
                    cost: item.cost * item.quantity
                });
            }
        });
        
        // Add AV items
        avItems.forEach(item => {
            if (item.quantity > 0) {
                items.push({
                    name: item.name,
                    quantity: item.quantity,
                    cost: item.cost * item.quantity
                });
            }
        });
        
        // Add meal items
        mealItems.forEach(item => {
            if (item.selected && item.attendees > 0) {
                items.push({
                    name: `${item.name} (${item.attendees} attendees)`,
                    quantity: 1,
                    cost: item.cost * item.attendees
                });
            }
        });
        
        return items;
    };

    const items = getItemsFromTotalCost();

    const ItemsDisplay = ({ items }) => {
        return (
            <div className="items-display">
                {items.length === 0 ? (
                    <p>No items selected.</p>
                ) : (
                    <ul>
                        {items.map((item, index) => (
                            <li key={index}>
                                <span>{item.name}</span>
                                {item.quantity > 1 && <span> x{item.quantity}</span>}
                                <span> - ${item.cost}</span>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        );
    };

    const calculateTotalCost = (section) => {
        let totalCost = 0;
        if (section === "venue") {
          venueItems.forEach((item) => {
            totalCost += item.cost * item.quantity;
          });
        } else if (section === "av") {
          avItems.forEach((item) => {
            totalCost += item.cost * item.quantity;
          });
        } else if (section === "meals") {
          mealItems.forEach((item) => {
            if (item.selected) {
              totalCost += item.cost * item.attendees;
            }
          });
        } else if (section === "all") {
          // Calculate total for all sections
          const venueCost = calculateTotalCost("venue");
          const avCost = calculateTotalCost("av");
          const mealsCost = calculateTotalCost("meals");
          totalCost = venueCost + avCost + mealsCost;
        }
        return totalCost;
    };

    const venueTotalCost = calculateTotalCost("venue");
    const avTotalCost = calculateTotalCost("av");
    const mealsTotalCost = calculateTotalCost("meals");
    const totalCosts = {
        venueCost: venueTotalCost,
        avCost: avTotalCost,
        mealsCost: mealsTotalCost,
        totalCost: calculateTotalCost("all")
    };

    const navigateToProducts = (idType) => {
        if (idType == '#venue' || idType == '#addons' || idType == '#meals') {
          if (showItems) { // Check if showItems is false
            setShowItems(false); // Set showItems to false to show the main sections
          }
        }
    }

    return (
        <>
            <navbar className="navbar_event_conference">
                <div className="company_logo">Conference Expense Planner</div>
                <div className="left_navbar">
                    <div className="nav_links">
                        <a href="#venue" onClick={() => navigateToProducts("#venue")} >Venue</a>
                        <a href="#addons" onClick={() => navigateToProducts('#addons')}>Add-ons</a>
                        <a href="#meals" onClick={() => navigateToProducts('#meals')}>Meals</a>
                    </div>
                    <button className="details_button" onClick={() => setShowItems(!showItems)}>
                        {showItems ? "Hide Details" : "Show Details"}
                    </button>
                </div>
            </navbar>
            <div className="main_container">
                {!showItems
                    ?
                    (
                        <div className="items-information">
                            <div id="venue" className="venue_container container_main">
                                <div className="text">
                                    <h1>Venue Room Selection</h1>
                                </div>
                                <div className="venue_selection">
                                    {venueItems.map((item, index) => (
                                        <div className="venue_main" key={index}>
                                            <div className="img">
                                                <img src={item.img} alt={item.name} />
                                            </div>
                                            <div className="text">{item.name}</div>
                                            <div>${item.cost}</div>
                                            <div className="button_container">
                                                {item.name === "Auditorium Hall (Capacity:200)" ? (
                                                    <>
                                                        <button
                                                            className={item.quantity === 0 ? "btn-warning btn-disabled" : "btn-minus btn-warning"}
                                                            onClick={() => handleRemoveFromCart(index)}
                                                        >
                                                            &#8211;
                                                        </button>
                                                        <span className="selected_count">
                                                            {item.quantity > 0 ? ` ${item.quantity}` : "0"}
                                                        </span>
                                                        <button
                                                            className={remainingAuditoriumQuantity === 0 ? "btn-success btn-disabled" : "btn-success btn-plus"}
                                                            onClick={() => handleAddToCart(index)}
                                                        >
                                                            &#43;
                                                        </button>
                                                    </>
                                                ) : (
                                                    <>
                                                        <button
                                                            className={item.quantity === 0 ? "btn-warning btn-disabled" : "btn-warning btn-plus"}
                                                            onClick={() => handleRemoveFromCart(index)}
                                                        >
                                                            &#8211;
                                                        </button>
                                                        <span className="selected_count">
                                                            {item.quantity > 0 ? ` ${item.quantity}` : "0"}
                                                        </span>
                                                        <button
                                                            className={item.quantity === 10 ? "btn-success btn-disabled" : "btn-success btn-plus"}
                                                            onClick={() => handleAddToCart(index)}
                                                        >
                                                            &#43;
                                                        </button>
                                                    </>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                                <div className="total_cost">Total Cost: ${venueTotalCost}</div>
                            </div>

                            {/*Necessary Add-ons*/}
                            <div id="addons" className="venue_container container_main">
                                <div className="text">
                                    <h1>Add-ons Selection</h1>
                                </div>
                                <div className="addons_selection">
                                    {avItems.map((item, index) => (
                                        <div className="venue_main" key={index}>
                                            <div className="img">
                                                <img src={item.img} alt={item.name} />
                                            </div>
                                            <div className="text">{item.name}</div>
                                            <div>${item.cost}</div>
                                            <div className="button_container">
                                                <button
                                                    className={item.quantity === 0 ? "btn-warning btn-disabled" : "btn-warning btn-plus"}
                                                    onClick={() => handleDecrementAvQuantity(index)}
                                                >
                                                    &#8211;
                                                </button>
                                                <span className="selected_count">
                                                    {item.quantity > 0 ? ` ${item.quantity}` : "0"}
                                                </span>
                                                <button
                                                    className="btn-success btn-plus"
                                                    onClick={() => handleIncrementAvQuantity(index)}
                                                >
                                                    &#43;
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                                <div className="total_cost">Total Cost: ${avTotalCost}</div>
                            </div>

                            {/* Meal Section */}
                            <div id="meals" className="venue_container container_main">
                                <div className="text">
                                    <h1>Meals Selection</h1>
                                </div>
                                <div className="input-container venue_selection">
                                    <label htmlFor="numberOfPeople">Number of Attendees:</label>
                                    <input 
                                        type="number" 
                                        id="numberOfPeople" 
                                        min="1" 
                                        value={numberOfPeople} 
                                        onChange={(e) => setNumberOfPeople(Math.max(1, parseInt(e.target.value) || 1))}
                                    />
                                </div>
                                <div className="meal_selection">
                                    {mealItems.map((item, index) => (
                                        <div className="meal_item" key={index}>
                                            <div className="meal_info">
                                                <input
                                                    type="checkbox"
                                                    id={`meal-${index}`}
                                                    checked={item.selected}
                                                    onChange={() => handleMealSelection(index)}
                                                />
                                                <label htmlFor={`meal-${index}`}>{item.name} - ${item.cost}/person</label>
                                            </div>
                                            {item.selected && (
                                                <div className="attendees-input">
                                                    <label htmlFor={`attendees-${index}`}>Attendees:</label>
                                                    <input
                                                        type="number"
                                                        id={`attendees-${index}`}
                                                        min="1"
                                                        value={item.attendees}
                                                        onChange={(e) => handleAttendeeChange(index, e.target.value)}
                                                    />
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                                <div className="total_cost">Total Cost: ${mealsTotalCost}</div>
                            </div>
                        </div>
                    ) : (
                        <div className="total_amount_detail">
                            <TotalCost totalCosts={totalCosts} handleClick={handleToggleItems} ItemsDisplay={() => <ItemsDisplay items={items} />} />
                        </div>
                    )
                }
            </div>
        </>
    );
};

export default ConferenceEvent;
