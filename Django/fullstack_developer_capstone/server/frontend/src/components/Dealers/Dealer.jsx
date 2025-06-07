import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { buildApiUrl } from '../../config';
import "./Dealers.css";
import "../assets/style.css";
import review_icon from "../assets/reviewicon.png"

const Dealer = () => {
  const [dealer, setDealer] = useState({});
  const [reviews, setReviews] = useState([]);
  const [unreviewed, setUnreviewed] = useState(false);
  const [postReview, setPostReview] = useState(<></>)
  let curr_url = window.location.href;
  let root_url = curr_url.substring(0,curr_url.indexOf("dealer"));
  let params = useParams();
  let id =params.id;
  let dealer_url = buildApiUrl(`/djangoapp/dealer/${id}`);
  let reviews_url = buildApiUrl(`/djangoapp/reviews/dealer/${id}`);
  let post_review = buildApiUrl(`/postreview/${id}`);
  
  const get_dealer = async ()=>{
    const res = await fetch(dealer_url, {
      method: "GET"
    });
    const retobj = await res.json();
    
    if(res.ok && retobj.status === 200) {
      setDealer(retobj.dealer);
    }
  }

  const get_reviews = async ()=>{
    const res = await fetch(reviews_url, {
      method: "GET"
    });
    const retobj = await res.json();
    
    if(res.ok && retobj.status === 200) {
      if(retobj.reviews.length > 0){
        setReviews(retobj.reviews)
      } else {
        setUnreviewed(true);
      }
    }
  }

  const senti_icon = (sentiment)=>{
    let icon = sentiment === "positive"?"👍":"👎";
    if(sentiment === "neutral")
      icon = "🤷‍♂️";
    return icon
  }

  useEffect(() => {
    get_dealer();
    get_reviews();
    if(sessionStorage.getItem("username")) {
      setPostReview(<a href={post_review}><img src={review_icon} style={{width:'10%',marginLeft:'10px',marginTop:'10px'}} alt='Post Review'/></a>)
    }
  }, []);

return(
  <div style={{margin:"20px"}}>
    <div style={{marginTop:"10px"}}>
      <h1 style={{color:"grey"}}>{dealer.full_name}{postReview}</h1>
      <h4 style={{color:"grey"}}>{dealer.city},{dealer.address}, Zip - {dealer.zip}, {dealer.state}</h4>
    </div>
    <div className="reviews_panel">
    {reviews.length === 0 && unreviewed === false ? (
      <text>Loading Reviews....</text>
    ):(
      <>
      {unreviewed ? (
        <div>No reviews yet! </div>
      ):(
        <div className="reviews_container">
        {reviews.map(review => (
          <div className='review_panel' key={review.id}>
            <img src={review_icon} className="review_icon" alt='Review'/>
            <div className='review'>
              <div className="review_header">
                <span className="reviewer_name">{review.name}</span>
                <span className={`sentiment_badge ${review.sentiment}`}>
                  {senti_icon(review.sentiment)} {review.sentiment}
                </span>
              </div>
              <div className="reviewText">
                {review.review}
              </div>
              {review.purchase ? (
                <div className="purchase_info">
                  <div>Purchase: {review.purchase_date}</div>
                  <div>Car: {review.car_make} {review.car_model} {review.car_year}</div>
                </div>
              ):(<></>)}
            </div>
          </div>
        ))}
        </div>
      )}
      </>
    )}
    </div>
  </div>
)
}
export default Dealer
