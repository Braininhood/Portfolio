# Coupons: Where to Create, Where to Use, What Is Saved

## Where to create coupons

You can create and manage coupons in two places:

1. **App admin (recommended)**  
   - Go to **Admin → Coupons** in the app (or `/ad/coupons`).  
   - Use **Create Coupon** to add a new code; you can edit or delete from the list.  
   - Set code, name, discount type (percentage or fixed), value, validity dates, usage limits, minimum order amount, and optional service restrictions.

2. **Django admin**  
   - Go to `/admin/` and open **Coupons → Coupons**.  
   - Create or edit coupons there; same data as the app admin.

## Where customers use coupons

- **Booking payment step**  
  On the booking payment page there is a “Have a Coupon Code?” section. The customer enters the code, applies it, and the discount is shown and applied to the order total. Coupons apply to **one-time orders** only (not to subscription creation in the current implementation).

- **Customer dashboard**  
  Logged-in customers see a **Current offers** section on their dashboard (`/cus/dashboard`) that lists active coupon codes and a short description. They can use those codes when they go to **Book & use** (booking flow → payment step).

## What is saved in the database

### Coupon (main record)

- **Table:** `coupons_coupon`
- **Stored:** `code`, `name`, `discount_type`, `discount_value`, `max_uses`, `max_uses_per_customer`, `used_count`, `valid_from`, `valid_until`, `minimum_order_amount`, `status`, `description`, and relations to applicable/excluded services.
- **Updated when:** You create or edit a coupon in admin (app or Django). When a coupon is used, only `used_count` is incremented; other fields change only when you edit the coupon.

### CouponUsage (each use)

- **Table:** `coupons_couponusage`
- **Stored per use:** Which coupon was used; which customer (or guest email); which order (or subscription/appointment); `discount_amount`, `order_amount`, `final_amount`; timestamp.
- **Created when:** A customer applies a valid coupon at order creation. One row per use; `coupon.used_count` is incremented at the same time.

### Order

- **Table:** `orders_order`
- **Stored:** `total_price` is the **already discounted** amount. The order row does **not** store `coupon_code` or `discount_amount`; those come from the related **CouponUsage** (and from the API field `coupon_used` on the order, which is derived from CouponUsage for display).

So: **what is saved** for coupons is the **Coupon** row (definition), **CouponUsage** rows (one per use, with amounts), and the order’s **total_price** (already reduced). **What changes in the DB** when a coupon is used: one new **CouponUsage** row and **coupon.used_count** incremented by one.

## Order display: seeing which coupon was used

The order API includes a read-only **`coupon_used`** field (when a coupon was applied), with:

- `code` – coupon code used  
- `discount_amount` – discount applied  

So order detail/confirmation pages can show e.g. “Discount (SAVE20): £5.00” using this field.
