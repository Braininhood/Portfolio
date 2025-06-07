import { createSlice } from "@reduxjs/toolkit";

export const avSlice = createSlice({
  name: "av",
  initialState: [
    {
      img: "https://pixabay.com/images/download/projector-292748_640.jpg",
      name: "Projector",
      cost: 250,
      quantity: 0,
    },
    {
      img: "https://pixabay.com/images/download/microphone-3315985_640.jpg",
      name: "Microphone",
      cost: 50,
      quantity: 0,
    },
    {
      img: "https://pixabay.com/images/download/speaker-759793_640.jpg",
      name: "Speaker",
      cost: 150,
      quantity: 0,
    },
    {
      img: "https://pixabay.com/images/download/laptop-336373_640.jpg",
      name: "Laptop",
      cost: 200,
      quantity: 0,
    },
    {
      img: "https://pixabay.com/images/download/screen-1315650_640.jpg",
      name: "Presentation Screen",
      cost: 100,
      quantity: 0,
    },
  ],

  reducers: {
    incrementAvQuantity: (state, action) => {
      const { payload: index } = action;
      if (state[index]) {
        state[index].quantity++;
      }
    },
    decrementAvQuantity: (state, action) => {
      const { payload: index } = action;
      if (state[index] && state[index].quantity > 0) {
        state[index].quantity--;
      }
    },
  },
});

export const { incrementAvQuantity, decrementAvQuantity } = avSlice.actions;

export default avSlice.reducer;
