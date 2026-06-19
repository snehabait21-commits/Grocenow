// Simple cart & wishlist handling using localStorage for GroceNow theme
// Works on product listing pages (shop, related products), product-single and navbar cart icon.

(function () {
  const CART_KEY_BASE = 'grocenow_cart';
  const WISHLIST_KEY_BASE = 'grocenow_wishlist';

  function getTokenPayloadEmail() {
    try {
      var token = localStorage.getItem('token');
      if (!token || token.split('.').length < 2) return '';
      var part = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
      var json = JSON.parse(atob(part));
      return (json.email || '').toLowerCase();
    } catch (_) {
      return '';
    }
  }

  function getUserScope() {
    try {
      var user = JSON.parse(localStorage.getItem('customer_user') || '{}');
      if (user && user.email) return String(user.email).toLowerCase();
    } catch (_) {}
    return getTokenPayloadEmail() || 'guest';
  }

  function getCartKey() {
    return CART_KEY_BASE + '_' + getUserScope();
  }

  function getWishlistKey() {
    return WISHLIST_KEY_BASE + '_' + getUserScope();
  }

  function load(key) {
    try {
      const raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      console.warn('Failed to read', key, e);
      return [];
    }
  }

  function save(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
      console.warn('Failed to save', key, e);
    }
  }

  function parsePrice(text) {
    if (!text) return 0;
    const num = parseFloat(text.replace(/[^0-9.]/g, ''));
    return isNaN(num) ? 0 : num;
  }

  function slug(str) {
    return (str || '')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '');
  }

  function getProductFromCard(card) {
    const nameEl = card.querySelector('.text h3 a, .product-name h3');
    const name = nameEl ? nameEl.textContent.trim() : 'Product';
    const priceEl =
      card.querySelector('.price .price-sale') ||
      card.querySelector('.price span:last-child') ||
      card.querySelector('.price span');
    const priceText = priceEl ? priceEl.textContent : '0';
    const price = parsePrice(priceText);
    const imgEl = card.querySelector('img');
    const image = imgEl ? imgEl.getAttribute('src') : '';
    const id = slug(name);
    // shop.html wraps each product with: data-type="product" data-category="fruits|vegetables|..."
    const catWrap = card.closest('[data-type="product"][data-category]') || card.closest('[data-category]');
    const categorySlug = catWrap ? catWrap.getAttribute('data-category') : '';
    return { id, name, price, image, categorySlug };
  }

  let cart = load(getCartKey());
  let wishlist = load(getWishlistKey());

  function reloadCart() {
    cart = load(getCartKey());
  }

  function reloadWishlist() {
    wishlist = load(getWishlistKey());
  }

  function updateCartBadge() {
    // Always reload cart from localStorage to ensure we have latest data
    reloadCart();
    const totalQty = cart.reduce((sum, item) => sum + (item.qty || 1), 0);
    // Navbar cart count [x] - try multiple selectors to catch all navbar variations
    var selectors = [
      '.nav-item.cta a',
      '.nav-item.cta-colored a',
      'a[href*="cart.html"]',
      '.navbar-nav a[href*="cart"]'
    ];
    selectors.forEach(function(sel) {
      document.querySelectorAll(sel).forEach(function (a) {
        if (a.querySelector('.icon-shopping_cart') || a.textContent.indexOf('cart') !== -1) {
          var cartIcon = a.querySelector('.icon-shopping_cart');
          if (cartIcon) {
            a.innerHTML = '<span class="icon-shopping_cart"></span>[' + totalQty + ']';
          } else if (a.textContent.match(/\[.*\]/)) {
            // Update existing [x] pattern
            a.innerHTML = a.innerHTML.replace(/\[.*\]/, '[' + totalQty + ']');
          }
        }
      });
    });
  }

  function showToast(message) {
    let toast = document.querySelector('.gc-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.className = 'gc-toast';
      toast.style.position = 'fixed';
      toast.style.right = '20px';
      toast.style.bottom = '20px';
      toast.style.background = '#0f172a';
      toast.style.color = '#f9fafb';
      toast.style.padding = '10px 16px';
      toast.style.borderRadius = '999px';
      toast.style.fontSize = '14px';
      toast.style.boxShadow = '0 10px 25px rgba(15,23,42,0.35)';
      toast.style.zIndex = '9999';
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(20px)';
      toast.style.transition = 'opacity 0.2s ease, transform 0.2s ease';
      document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.style.opacity = '1';
    toast.style.transform = 'translateY(0)';
    clearTimeout(showToast._timer);
    showToast._timer = setTimeout(function () {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(20px)';
    }, 2200);
  }

  function getCurrentCustomer() {
    try {
      var user = JSON.parse(localStorage.getItem('customer_user') || '{}');
      if (user && user.email) return user;
    } catch (_) {}
    return null;
  }

  function initProfileDropdown() {
    var customer = getCurrentCustomer();
    if (!customer) return;

    var loginAnchor = document.querySelector('.navbar-nav a[href*="/login"], .navbar-nav a[href*="login"]');
    if (!loginAnchor) return;
    var loginItem = loginAnchor.closest('.nav-item');
    if (!loginItem) return;

    var fullName = (customer.name || customer.email || 'User').trim();
    var email = (customer.email || '').trim();

    // Inject scoped style once
    if (!document.getElementById('gc-profile-style')) {
      var css = document.createElement('style');
      css.id = 'gc-profile-style';
      css.textContent =
        '.gc-profile{position:relative;}' +
        '.gc-profile-btn{display:flex;align-items:center;gap:8px;color:#111827!important;cursor:pointer;}' +
        '.gc-profile-btn .gc-user-icon{font-size:15px;line-height:1;}' +
        '.gc-profile-menu{position:absolute;top:110%;right:0;min-width:260px;background:#fff;border:1px solid #e5e7eb;border-radius:12px;box-shadow:0 12px 30px rgba(2,6,23,.18);padding:10px;z-index:99999;display:none;}' +
        '.gc-profile.open .gc-profile-menu{display:block;}' +
        '.gc-profile-head{padding:8px 10px;border-bottom:1px solid #f1f5f9;margin-bottom:6px;}' +
        '.gc-profile-name{font-size:14px;font-weight:700;color:#0f172a;line-height:1.2;}' +
        '.gc-profile-email{font-size:12px;color:#64748b;word-break:break-all;}' +
        '.gc-profile-link{display:block;padding:9px 10px;border-radius:8px;color:#0f172a;text-decoration:none;font-size:13px;}' +
        '.gc-profile-link:hover{background:#f8fafc;text-decoration:none;}' +
        '.gc-profile-link.logout{color:#b91c1c;}';
      document.head.appendChild(css);
    }

    loginItem.classList.add('gc-profile');
    loginItem.innerHTML =
      '<a href="#" class="nav-link gc-profile-btn" id="gcProfileToggle" aria-expanded="false" aria-haspopup="true">' +
        '<span class="icon-user gc-user-icon"></span>' +
      '</a>' +
      '<div class="gc-profile-menu" id="gcProfileMenu">' +
        '<div class="gc-profile-head">' +
          '<div class="gc-profile-name">' + fullName + '</div>' +
          '<div class="gc-profile-email">' + email + '</div>' +
        '</div>' +
        '<a class="gc-profile-link" href="/account">My account</a>' +
        '<a class="gc-profile-link" href="/signup">Add account</a>' +
        '<a class="gc-profile-link logout" href="/logout" id="gcLogoutLink">Logout</a>' +
      '</div>';

    var toggle = document.getElementById('gcProfileToggle');
    var menuWrap = loginItem;
    var logoutLink = document.getElementById('gcLogoutLink');

    if (toggle) {
      toggle.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        menuWrap.classList.toggle('open');
      });
    }

    document.addEventListener('click', function (e) {
      if (!menuWrap.contains(e.target)) {
        menuWrap.classList.remove('open');
      }
    });

    if (logoutLink) {
      logoutLink.addEventListener('click', function () {
        // Clear browser-side auth and cart state for current user
        try {
          var cartKey = getCartKey();
          var wishlistKey = getWishlistKey();
          localStorage.removeItem(cartKey);
          localStorage.removeItem(wishlistKey);
          localStorage.removeItem('token');
          localStorage.removeItem('customer_user');
        } catch (_) {}
      });
    }
  }

  function showLogoutMessageIfNeeded() {
    try {
      var params = new URLSearchParams(window.location.search || '');
      if (params.get('logout') === '1') {
        showToast('You logged out successfully.');
      }
    } catch (_) {}
  }

  function addToCart(product) {
    if (!product || !product.id) return;

    var token = localStorage.getItem('token');
    if (!token) {
      showToast('Please login to add items to cart.');
      window.location.href = '/login';
      return;
    }

    var existing = cart.find(function (p) {
      return p.id === product.id;
    });
    if (existing) {
      existing.qty = (existing.qty || 1) + 1;
    } else {
      cart.push({
        id: product.id,
        name: product.name,
        price: product.price,
        image: product.image,
        categorySlug: product.categorySlug || '',
        productId: product.dbId || null,
        qty: 1
      });
    }
    save(getCartKey(), cart);
    updateCartBadge();
    showToast('Added to cart');

    var dbId = product.dbId;
    if (dbId) {
      fetch('/api/user/cart', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + token
        },
        body: JSON.stringify({
          product_id: parseInt(dbId, 10),
          quantity: 1
        })
      }).catch(function (err) {
        console.warn('Failed to sync cart to server', err);
      });
    }
  }

  function toggleWishlist(product, heartEl) {
    const idx = wishlist.findIndex(function (p) {
      return p.id === product.id;
    });
    let added = false;
    if (idx >= 0) {
      wishlist.splice(idx, 1);
      added = false;
      if (heartEl) heartEl.classList.remove('gc-heart-active');
    } else {
      wishlist.push(product);
      added = true;
      if (heartEl) heartEl.classList.add('gc-heart-active');
    }
    save(getWishlistKey(), wishlist);
    showToast(added ? 'Added to wishlist' : 'Removed from wishlist');
  }

  function initHearts() {
    document
      .querySelectorAll('.product .heart, .related-products .heart')
      .forEach(function (heart) {
        const card = heart.closest('.product');
        if (!card) return;
        const product = getProductFromCard(card);
        if (
          wishlist.some(function (p) {
            return p.id === product.id;
          })
        ) {
          heart.classList.add('gc-heart-active');
        }
        heart.addEventListener('click', function (e) {
          e.preventDefault();
          toggleWishlist(product, heart);
        });
      });
  }

  function initCartButtons() {
    // Listing & related products
    document.querySelectorAll('.product').forEach(function (card) {
      const product = getProductFromCard(card);
      const cartBtns = card.querySelectorAll(
        '.buy-now, .add-to-cart'
      );
      cartBtns.forEach(function (btn) {
        btn.addEventListener('click', function (e) {
          e.preventDefault();
          var p = Object.assign({}, product);
          var dbId = btn.getAttribute('data-id');
          if (!dbId) {
            var addBtn = card.querySelector('.add-to-cart[data-id]');
            if (addBtn) dbId = addBtn.getAttribute('data-id');
          }
          if (dbId) p.dbId = parseInt(dbId, 10);
          addToCart(p);
        });
      });
    });

    // Single product main Add to Cart
    const details = document.querySelector('.product-details');
    if (details) {
      const addBtn = details.querySelector('.btn.btn-black');
      if (addBtn) {
        addBtn.addEventListener('click', function (e) {
          e.preventDefault();
          const nameEl = details.querySelector('h3');
          const name = nameEl ? nameEl.textContent.trim() : 'Product';
          const priceEl = details.querySelector('.price span');
          const price = parsePrice(priceEl ? priceEl.textContent : '0');
          const mainImg =
            document.querySelector('.product img') ||
            document.querySelector('.img-prod img');
          const image = mainImg ? mainImg.getAttribute('src') : '';
          const product = {
            id: slug(name),
            name: name,
            price: price,
            image: image,
          };
          addToCart(product);
        });
      }
    }
  }

  function renderCartPage() {
    var path = window.location.pathname || '';
    if (!path.endsWith('/cart') && path.indexOf('cart.html') === -1) return;
    reloadCart(); // Reload cart from localStorage
    var tbody = document.querySelector('.cart-list table tbody, .cart-wrap table tbody, table.table tbody');
    if (!tbody) return;
    tbody.innerHTML = '';

    cart.forEach(function (item) {
      var tr = document.createElement('tr');
      tr.className = 'text-center';
      tr.dataset.id = item.id;
      var lineTotal = (item.price || 0) * (item.qty || 1);
      tr.innerHTML =
        '<td class="product-remove"><a href="#" data-action="remove"><span class="ion-ios-close"></span></a></td>' +
        '<td class="image-prod"><div class="img" style="background-image:url(' +
        (item.image || 'images/product-1.jpg') +
        ');"></div></td>' +
        '<td class="product-name"><h3>' +
        item.name +
        '</h3><p>In your cart</p></td>' +
        '<td class="price">₹' +
        item.price +
        '</td>' +
        '<td class="quantity"><div class="input-group mb-3">' +
        '<div class="input-group-prepend"><button class="btn btn-outline-secondary gc-qty-minus" type="button">−</button></div>' +
        '<input type="text" class="quantity form-control input-number gc-qty-input" value="' +
        (item.qty || 1) +
        '" min="1" max="100">' +
        '<div class="input-group-append"><button class="btn btn-outline-secondary gc-qty-plus" type="button">+</button></div>' +
        '</div></td>' +
        '<td class="total">₹' +
        lineTotal +
        '</td>';
      tbody.appendChild(tr);
    });

    function recalcTotals() {
      var subtotal = cart.reduce(function (sum, it) {
        return sum + (it.price || 0) * (it.qty || 1);
      }, 0);
      var delivery = 0;
      var discount = 0;
      var total = subtotal + delivery - discount;
      var setText = function (id, val) {
        var el = document.getElementById(id);
        if (el) el.textContent = '₹' + val.toFixed(0);
      };
      setText('cart-subtotal', subtotal);
      setText('cart-delivery', delivery);
      setText('cart-discount', discount);
      setText('cart-total', total);
    }

    function bindRowEvents() {
      tbody.querySelectorAll('tr').forEach(function (tr) {
        var id = tr.dataset.id;
        var removeBtn = tr.querySelector('[data-action=\"remove\"]');
        if (removeBtn) {
          removeBtn.addEventListener('click', function (e) {
            e.preventDefault();
            cart = cart.filter(function (p) {
              return p.id !== id;
            });
            save(getCartKey(), cart);
            updateCartBadge();
            renderCartPage();
          });
        }
        var minus = tr.querySelector('.gc-qty-minus');
        var plus = tr.querySelector('.gc-qty-plus');
        var input = tr.querySelector('.gc-qty-input');
        function updateQty(newQty) {
          if (newQty < 1) newQty = 1;
          input.value = newQty;
          var item = cart.find(function (p) {
            return p.id === id;
          });
          if (item) item.qty = newQty;
          save(getCartKey(), cart);
          updateCartBadge();
          tr.querySelector('.total').textContent = '₹' + ((item.price || 0) * newQty).toFixed(0);
          recalcTotals();
        }
        if (minus) {
          minus.addEventListener('click', function () {
            var current = parseInt(input.value, 10) || 1;
            updateQty(current - 1);
          });
        }
        if (plus) {
          plus.addEventListener('click', function () {
            var current = parseInt(input.value, 10) || 1;
            updateQty(current + 1);
          });
        }
        if (input) {
          input.addEventListener('change', function () {
            var val = parseInt(input.value, 10);
            if (isNaN(val) || val < 1) val = 1;
            updateQty(val);
          });
        }
      });
      recalcTotals();
    }

    bindRowEvents();
  }

  function renderWishlistPage() {
    var path = window.location.pathname || '';
    if (!path.endsWith('/wishlist') && path.indexOf('wishlist.html') === -1) return;
    reloadWishlist(); // Reload wishlist from localStorage
    var tbody = document.querySelector('.cart-list table tbody, table.table tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    wishlist.forEach(function (item) {
      var tr = document.createElement('tr');
      tr.className = 'text-center';
      tr.dataset.id = item.id;
      tr.innerHTML =
        '<td class=\"product-remove\"><a href=\"#\" data-action=\"remove\"><span class=\"ion-ios-close\"></span></a></td>' +
        '<td class=\"image-prod\"><div class=\"img\" style=\"background-image:url(' +
        (item.image || 'images/product-1.jpg') +
        ');\"></div></td>' +
        '<td class=\"product-name\"><h3>' +
        item.name +
        '</h3><p>Saved for later</p></td>' +
        '<td class=\"price\">₹' +
        (item.price || 0) +
        '</td>' +
        '<td class=\"quantity\">1</td>' +
        '<td class=\"total\">₹' +
        (item.price || 0) +
        '</td>';
      tbody.appendChild(tr);
    });
    tbody.querySelectorAll('[data-action=\"remove\"]').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        var tr = btn.closest('tr');
        var id = tr.dataset.id;
        wishlist = wishlist.filter(function (p) {
          return p.id !== id;
        });
        save(getWishlistKey(), wishlist);
        tr.remove();
        showToast('Removed from wishlist');
      });
    });
  }

  function renderCheckoutPage() {
    var path = window.location.pathname || '';
    if (!path.endsWith('/checkout') && path.indexOf('checkout.html') === -1) return;
    reloadCart(); // Reload cart from localStorage
    
    // Update checkout totals from cart
    var subtotal = cart.reduce(function (sum, it) {
      return sum + (it.price || 0) * (it.qty || 1);
    }, 0);
    var delivery = 0;
    var discount = 0;
    var total = subtotal + delivery - discount;
    
    var setText = function (id, val) {
      var el = document.getElementById(id);
      if (el) el.textContent = '₹' + val.toFixed(0);
    };
    setText('checkout-subtotal', subtotal);
    setText('checkout-delivery', delivery);
    setText('checkout-discount', discount);
    setText('checkout-total', total);

    // Handle Place Order button
    var placeOrderBtn = document.getElementById('place-order-btn');
    if (placeOrderBtn) {
      placeOrderBtn.addEventListener('click', function (e) {
        e.preventDefault();
        
        // Basic validation - check required fields
        var requiredFields = [
          { id: 'checkout-firstname', name: 'First Name' },
          { id: 'checkout-lastname', name: 'Last Name' },
          { id: 'checkout-country', name: 'Country' },
          { id: 'checkout-address', name: 'Street Address' },
          { id: 'checkout-city', name: 'Town / City' },
          { id: 'checkout-postcode', name: 'Postcode / ZIP' },
          { id: 'checkout-phone', name: 'Phone' },
          { id: 'checkout-email', name: 'Email Address' }
        ];
        
        var isValid = true;
        var missingFields = [];
        
        requiredFields.forEach(function (field) {
          var el = document.getElementById(field.id);
          if (el) {
            var value = el.value ? el.value.trim() : '';
            if (field.id === 'checkout-country') {
              // For select, check if a value is selected
              if (!value || value === '') {
                isValid = false;
                missingFields.push(field.name);
              }
            } else {
              if (!value) {
                isValid = false;
                missingFields.push(field.name);
              }
            }
          }
        });
        
        // Check email format if provided
        var emailEl = document.getElementById('checkout-email');
        if (emailEl && emailEl.value) {
          var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
          if (!emailRegex.test(emailEl.value.trim())) {
            isValid = false;
            missingFields.push('Valid Email Address');
          }
        }
        
        if (!isValid) {
          showToast('Please fill all required fields: ' + missingFields.join(', '));
          return;
        }
        
        // Check if cart is empty
        if (cart.length === 0) {
          showToast('Your cart is empty. Add items before placing an order.');
          return;
        }

        // Try to persist order in backend (if logged in)
        var token = localStorage.getItem('token');
        if (!token) {
          showToast('Please login to place an order.');
          return;
        }

        var payload = {
          items: cart.map(function (it) {
            return {
              name: it.name,
              price: it.price,
              quantity: it.qty || 1,
              category: it.categorySlug || null,
              product_id: it.productId || null
            };
          })
        };

        fetch('/api/user/frontend-orders', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + token
          },
          body: JSON.stringify(payload)
        })
          .then(function (res) { return res.json().then(function (d) { return { ok: res.ok, data: d }; }); })
          .then(function (result) {
            if (!result.ok) {
              showToast(result.data && result.data.error ? result.data.error : 'Failed to save order.');
              return;
            }

            // Show success message
            showToast('✅ Your order has been placed successfully!');
            
            // Clear cart from localStorage
            cart = [];
            save(getCartKey(), cart);
            
            // Reset cart count
            updateCartBadge();
            
            // Redirect to home page after 2 seconds
            setTimeout(function () {
              window.location.href = '/';
            }, 2000);
          })
          .catch(function () {
            showToast('Failed to contact server. Order not saved.');
          });
      });
    }
  }

  function initPage() {
    // Always reload cart and wishlist from localStorage on every page load
    reloadCart();
    reloadWishlist();
    
    // Heart active styling (CSS hook)
    var styleTag = document.createElement('style');
    styleTag.textContent =
      '.product .heart.gc-heart-active span i{color:#e11d48;}';
    document.head.appendChild(styleTag);

    initCartButtons();
    initHearts();
    initProfileDropdown();
    showLogoutMessageIfNeeded();
    updateCartBadge(); // Update badge on every page load
    renderCartPage();
    renderWishlistPage();
    renderCheckoutPage();
  }

  // Run on DOMContentLoaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPage);
  } else {
    // DOM already loaded, run immediately
    initPage();
  }

  // Also update badge after a short delay to catch late-loading navbars
  setTimeout(function() {
    updateCartBadge();
  }, 100);
})();