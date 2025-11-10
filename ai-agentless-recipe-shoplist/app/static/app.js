// AI Recipe Shoplist Crawler - Frontend JavaScript

class RecipeShoplistApp {
  constructor() {
    this.apiBase = "/api/v1";
    this.currentRecipe = null;
    this.currentOptimization = null;
    this.currentProducts = [];
    this.ingredientProductMap = new Map();
    this.demoManager = null;
    this.init();
  }

  init() {
    // Initialize demo manager
    this.demoManager = new DemoManager(this);
    this.setupEventListeners();
    this.checkUrlParams();
  }

  setupEventListeners() {
    // Recipe form submission
    const form = document.getElementById("recipeForm");
    if (form) {
      form.addEventListener("submit", (e) => this.handleRecipeSubmit(e));
    }

    // Demo button
    window.loadDemo = () => this.demoManager.loadDemo();

    // Store selection
    this.setupStoreSelection();
  }

  setupStoreSelection() {
    // Select All button
    const selectAllBtn = document.getElementById("selectAllStores");
    if (selectAllBtn) {
      selectAllBtn.addEventListener("click", () =>
        this.toggleSelectAllStores()
      );
    }

    // Individual store checkboxes
    const storeCheckboxes = document.querySelectorAll(".store-checkbox");
    storeCheckboxes.forEach((checkbox) => {
      checkbox.addEventListener("change", () => this.updateSelectAllButton());
    });
  }

  toggleSelectAllStores() {
    const storeCheckboxes = document.querySelectorAll(".store-checkbox");
    const selectAllBtn = document.getElementById("selectAllStores");

    // Check if all are currently selected
    const allSelected = Array.from(storeCheckboxes).every((cb) => cb.checked);

    // Toggle all checkboxes
    storeCheckboxes.forEach((checkbox) => {
      checkbox.checked = !allSelected;
    });

    // Update button text
    this.updateSelectAllButton();
  }

  updateSelectAllButton() {
    const storeCheckboxes = document.querySelectorAll(".store-checkbox");
    const selectAllBtn = document.getElementById("selectAllStores");

    if (!selectAllBtn) return;

    const allSelected = Array.from(storeCheckboxes).every((cb) => cb.checked);
    const noneSelected = Array.from(storeCheckboxes).every((cb) => !cb.checked);

    if (allSelected) {
      selectAllBtn.innerHTML = '<i class="fas fa-times me-1"></i>Deselect All';
      selectAllBtn.className = "btn btn-sm btn-outline-danger";
    } else if (noneSelected) {
      selectAllBtn.innerHTML =
        '<i class="fas fa-check-double me-1"></i>Select All';
      selectAllBtn.className = "btn btn-sm btn-outline-primary";
    } else {
      selectAllBtn.innerHTML =
        '<i class="fas fa-check-double me-1"></i>Select All';
      selectAllBtn.className = "btn btn-sm btn-outline-primary";
    }
  }

  getSelectedStores() {
    const storeCheckboxes = document.querySelectorAll(
      ".store-checkbox:checked"
    );
    return Array.from(storeCheckboxes).map((cb) => cb.value);
  }

  checkUrlParams() {
    const urlParams = new URLSearchParams(window.location.search);
    const demoParam = urlParams.get("demo");
    if (demoParam === "true") {
      this.demoManager.loadDemo();
    }
  }

  async handleRecipeSubmit(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const url = formData.get("url");

    if (!url) {
      this.showError("Please enter a recipe URL");
      return;
    }

    await this.processRecipe(url);
  }

  async processRecipe(url) {
    try {
      this.showLoading("Processing recipe...");
      this.hideResults();

      // Step 1: Process recipe
      const recipeResponse = await fetch(`${this.apiBase}/process-recipe`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: `url=${encodeURIComponent(url)}`,
      });

      const recipeResult = await recipeResponse.json();

      if (!recipeResult.success) {
        throw new Error(recipeResult.error || "Failed to process recipe");
      }

      this.currentRecipe = recipeResult.data.recipe;

      // Validate recipe data
      if (!this.currentRecipe || !this.currentRecipe.ingredients) {
        throw new Error("Recipe data is invalid or missing ingredients");
      }

      // Ensure ingredients is an array
      if (!Array.isArray(this.currentRecipe.ingredients)) {
        console.warn(
          "Ingredients is not an array, converting:",
          this.currentRecipe.ingredients
        );
        this.currentRecipe.ingredients = [];
      }

      console.log(
        `Recipe processed: ${this.currentRecipe.title || "Unknown"} with ${
          this.currentRecipe.ingredients.length
        } ingredients`
      );

      // Step 2: Get selected stores and validate
      const selectedStores = this.getSelectedStores();

      if (selectedStores.length === 0) {
        throw new Error("Please select at least one grocery store");
      }

      // Step 3: Search for products for each ingredient
      this.showLoading(
        `Finding products in ${selectedStores.length} store(s)...`
      );

      const searchResponse = await fetch(`${this.apiBase}/search-stores`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ingredients: this.currentRecipe.ingredients,
          stores: selectedStores,
        }),
      });

      const searchResult = await searchResponse.json();

      if (searchResult.success) {
        this.currentProducts = searchResult.products || [];
        // Map products to ingredients
        this.mapProductsToIngredients();
      } else {
        console.warn("Product search failed:", searchResult.error);
        this.currentProducts = [];
      }

      // Step 4: Display results with product images
      this.displayRecipeResults(recipeResult.data);
      this.hideLoading();
    } catch (error) {
      console.error("Error processing recipe:", error);
      this.showError(`Error: ${error.message}`);
      this.hideLoading();
    }
  }

  mapProductsToIngredients() {
    // Clear previous mapping
    this.ingredientProductMap.clear();

    // Map each product to its corresponding ingredient
    this.currentProducts.forEach((product) => {
      // Add null checks to prevent errors
      if (
        product &&
        product.ingredient &&
        typeof product.ingredient === "string"
      ) {
        const ingredientName = product.ingredient.toLowerCase();
        if (!this.ingredientProductMap.has(ingredientName)) {
          this.ingredientProductMap.set(ingredientName, []);
        }
        this.ingredientProductMap.get(ingredientName).push(product);
      } else {
        console.warn("Product missing ingredient property:", product);
      }
    });
  }

  displayRecipeResults(data) {
    const resultsSection = document.getElementById("resultsSection");
    const resultsContent = document.getElementById("resultsContent");

    if (!resultsSection || !resultsContent) return;

    const recipe = data.recipe;

    const html = `
            <!-- Recipe Information -->
            <div class="recipe-card fade-in">
                <div class="recipe-title">
                    <i class="fas fa-utensils me-2"></i>
                    ${recipe.title}
                </div>
                <div class="recipe-meta">
                    ${
                      recipe.servings
                        ? `<div class="meta-item"><i class="fas fa-users"></i> ${recipe.servings} servings</div>`
                        : ""
                    }
                    ${
                      recipe.prep_time
                        ? `<div class="meta-item"><i class="fas fa-clock"></i> ${recipe.prep_time}</div>`
                        : ""
                    }
                    ${
                      recipe.cook_time
                        ? `<div class="meta-item"><i class="fas fa-fire"></i> ${recipe.cook_time}</div>`
                        : ""
                    }
                </div>
                ${recipe.description ? `<p>${recipe.description}</p>` : ""}
                <a href="${
                  recipe.url
                }" target="_blank" class="btn btn-outline-primary btn-sm">
                    <i class="fas fa-external-link-alt me-1"></i>
                    View Original Recipe
                </a>
            </div>

            <!-- Ingredients List -->
            <div class="mb-4">
                <h5 class="mb-3">
                    <i class="fas fa-shopping-basket me-2"></i>
                    Ingredients (${
                      recipe.ingredients ? recipe.ingredients.length : 0
                    })
                </h5>
                <div class="ingredients-grid">
                    ${this.renderSimpleIngredients(recipe.ingredients || [])}
                </div>
            </div>

            <!-- Instructions -->
            ${
              recipe.instructions && recipe.instructions.length > 0
                ? `
            <div class="mb-4">
                <h5 class="mb-3">
                    <i class="fas fa-list-ol me-2"></i>
                    Instructions
                </h5>
                <ol class="list-group list-group-numbered">
                    ${recipe.instructions
                      .map(
                        (instruction) => `
                        <li class="list-group-item">${instruction}</li>
                    `
                      )
                      .join("")}
                </ol>
            </div>`
                : ""
            }

            <!-- Next Steps -->
            <div class="alert alert-info">
                <h6><i class="fas fa-info-circle me-2"></i>Next Steps</h6>
                <p class="mb-2">Recipe processed successfully! You can now:</p>
                <ul class="mb-0">
                    <li>Use the <a href="/api/v1/search-stores" target="_blank">Store Search API</a> to find products</li>
                    <li>Check the <a href="/api/v1/docs" target="_blank">API documentation</a> for more endpoints</li>
                </ul>
            </div>
        `;

    resultsContent.innerHTML = html;
    resultsSection.style.display = "block";
    resultsSection.scrollIntoView({ behavior: "smooth" });
  }

  renderSimpleIngredients(ingredients) {
    return ingredients
      .filter((ingredient) => ingredient && typeof ingredient === "object") // Filter out invalid ingredients
      .map((ingredient) => {
        // Safe access to ingredient properties with defaults
        const ingredientName = ingredient.name || "Unknown Ingredient";
        const quantityText = ingredient.quantity
          ? `${ingredient.quantity} ${ingredient.unit || ""}`.trim()
          : "As needed";

        // Get the best product for this ingredient
        const ingredientKey =
          ingredient && ingredient.name && typeof ingredient.name === "string"
            ? ingredient.name.toLowerCase()
            : "";
        const products = ingredientKey
          ? this.ingredientProductMap.get(ingredientKey) || []
          : [];
        const bestProduct = products.length > 0 ? products[0] : null;

        // Generate image section
        let imageSection;
        if (bestProduct) {
          // If we have a product, try to show its image or generate a placeholder
          const imageUrl =
            bestProduct.image_url ||
            this.generatePlaceholderImage(ingredientName);
          imageSection = `<div class="ingredient-image">
               <img src="${imageUrl}" 
                    alt="${ingredientName}" 
                    class="img-fluid rounded"
                    style="width: 80px; height: 80px; object-fit: cover;"
                    onerror="this.src='${this.generatePlaceholderImage(
                      ingredientName
                    )}'; this.onerror=null;">
             </div>`;
        } else {
          // No product found, show ingredient-themed placeholder
          const placeholderUrl = this.generatePlaceholderImage(ingredientName);
          imageSection = `<div class="ingredient-image">
               <img src="${placeholderUrl}" 
                    alt="${ingredientName}" 
                    class="img-fluid rounded"
                    style="width: 80px; height: 80px; object-fit: cover;"
                    onerror="this.style.display='none'; this.parentElement.innerHTML='<div class=&quot;ingredient-icon bg-secondary&quot;><i class=&quot;fas fa-question&quot;></i></div>';">
             </div>`;
        }

        // Generate product info section
        const productInfo = bestProduct
          ? `<div class="product-info">
               <small class="text-success">
                 <i class="fas fa-store me-1"></i>
                 ${bestProduct.store || "Unknown Store"} - $${(
              bestProduct.price || 0
            ).toFixed(2)}
               </small>
               <br>
               ${
                 bestProduct.url
                   ? `<a href="${
                       bestProduct.url
                     }" target="_blank" class="text-decoration-none">
                      <small class="text-primary">
                        <i class="fas fa-external-link-alt me-1"></i>
                        ${bestProduct.name || "Product name unavailable"}
                      </small>
                    </a>`
                   : `<small class="text-muted">${
                       bestProduct.name || "Product name unavailable"
                     }</small>`
               }
             </div>`
          : `<div class="product-info">
               <small class="text-warning">
                 <i class="fas fa-search me-1"></i>
                 No products found
               </small>
             </div>`;

        return `
                <div class="ingredient-item">
                    ${imageSection}
                    <div class="ingredient-details flex-grow-1">
                        <h6>${ingredientName}</h6>
                        <div class="ingredient-quantity">${quantityText}</div>
                        <small class="text-muted">${
                          ingredient.original_text || ""
                        }</small>
                        ${productInfo}
                    </div>
                </div>
            `;
      })
      .join("");
  }

  generatePlaceholderImage(ingredientName) {
    // Generate a consistent placeholder image based on ingredient name
    const hash = this.simpleHash(ingredientName);

    // Use a food-related image service with consistent seeds
    const seed = hash % 1000;

    // Try to get a food-themed image from Unsplash
    const foodKeywords = ["food", "ingredient", "grocery", "fresh", "kitchen"];
    const keyword = foodKeywords[hash % foodKeywords.length];

    return `https://source.unsplash.com/200x200/?${keyword}&sig=${seed}`;
  }
  simpleHash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    return Math.abs(hash);
  }

  displayResults(data) {
    const resultsSection = document.getElementById("resultsSection");
    const resultsContent = document.getElementById("resultsContent");

    if (!resultsSection || !resultsContent) return;

    const recipe = data.recipe;
    const optimization = data.optimization;
    const summary = data.summary;

    const html = `
            <!-- Recipe Information -->
            <div class="recipe-card fade-in">
                <div class="recipe-title">
                    <i class="fas fa-utensils me-2"></i>
                    ${recipe.title}
                </div>
                <div class="recipe-meta">
                    ${
                      recipe.servings
                        ? `<div class="meta-item"><i class="fas fa-users"></i> ${recipe.servings} servings</div>`
                        : ""
                    }
                    ${
                      recipe.prep_time
                        ? `<div class="meta-item"><i class="fas fa-clock"></i> ${recipe.prep_time}</div>`
                        : ""
                    }
                    ${
                      recipe.cook_time
                        ? `<div class="meta-item"><i class="fas fa-fire"></i> ${recipe.cook_time}</div>`
                        : ""
                    }
                </div>
                ${recipe.description ? `<p>${recipe.description}</p>` : ""}
            </div>

            <!-- Optimization Summary -->
            <div class="optimization-summary fade-in">
                <h4 class="mb-3">
                    <i class="fas fa-chart-line me-2"></i>
                    Optimization Results
                </h4>
                <div class="summary-stats">
                    <div class="stat-item">
                        <span class="stat-value">$${summary.total_cost.toFixed(
                          2
                        )}</span>
                        <span class="stat-label">Total Cost</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">${summary.stores_count}</span>
                        <span class="stat-label">Stores</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">${summary.items_found}/${
      summary.items_total
    }</span>
                        <span class="stat-label">Items Found</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">$${summary.savings.toFixed(
                          2
                        )}</span>
                        <span class="stat-label">Savings</span>
                    </div>
                </div>
            </div>

            <!-- Ingredients Grid -->
            <div class="mb-4">
                <h5 class="mb-3">
                    <i class="fas fa-shopping-basket me-2"></i>
                    Shopping List
                </h5>
                <div class="ingredients-grid">
                    ${this.renderIngredients(optimization.items)}
                </div>
            </div>

            <!-- Store Breakdown -->
            <div class="stores-breakdown">
                <h6 class="mb-3">
                    <i class="fas fa-store me-2"></i>
                    Store Breakdown
                </h6>
                ${this.renderStoreBreakdown(optimization.stores_breakdown)}
            </div>

            <!-- Action Buttons -->
            <div class="bill-actions">
                <button class="btn btn-success" onclick="app.generateBill('pdf')">
                    <i class="fas fa-file-pdf me-1"></i>
                    Generate PDF Bill
                </button>
                <button class="btn btn-outline-success" onclick="app.generateBill('html')">
                    <i class="fas fa-file-code me-1"></i>
                    Generate HTML Bill
                </button>
                <button class="btn btn-outline-primary" onclick="app.downloadJSON()">
                    <i class="fas fa-download me-1"></i>
                    Download JSON
                </button>
            </div>
        `;

    resultsContent.innerHTML = html;
    resultsSection.style.display = "block";
    resultsSection.scrollIntoView({ behavior: "smooth" });
  }

  renderIngredients(items) {
    return items
      .map((item) => {
        const ingredient = item.ingredient;
        const product = item.selected_product;
        const quantityText = ingredient.quantity
          ? `${ingredient.quantity} ${ingredient.unit || ""}`.trim()
          : "As needed";

        if (product) {
          return `
                    <div class="ingredient-item">
                        <div class="ingredient-icon">
                            <i class="fas fa-check"></i>
                        </div>
                        <div class="ingredient-details flex-grow-1">
                            <h6>${ingredient.name}</h6>
                            <div class="ingredient-quantity">${quantityText}</div>
                            <small class="text-muted">
                                ${product.store} - 
                                ${
                                  product.url
                                    ? `<a href="${
                                        product.url
                                      }" target="_blank" class="text-decoration-none text-primary">
                                       <i class="fas fa-external-link-alt me-1"></i>
                                       ${product.title || product.name}
                                     </a>`
                                    : product.title || product.name
                                } - $${product.price.toFixed(2)}
                            </small>
                        </div>
                        <div class="text-end">
                            <strong class="text-success">$${(
                              item.estimated_cost || 0
                            ).toFixed(2)}</strong>
                        </div>
                    </div>
                `;
        } else {
          return `
                    <div class="ingredient-item">
                        <div class="ingredient-icon bg-warning">
                            <i class="fas fa-exclamation"></i>
                        </div>
                        <div class="ingredient-details flex-grow-1">
                            <h6>${ingredient.name}</h6>
                            <div class="ingredient-quantity">${quantityText}</div>
                            <small class="text-danger">Not found in stores</small>
                        </div>
                        <div class="text-end">
                            <span class="text-muted">-</span>
                        </div>
                    </div>
                `;
        }
      })
      .join("");
  }

  renderStoreBreakdown(breakdown) {
    return Object.entries(breakdown)
      .map(
        ([store, cost]) => `
            <div class="store-item">
                <span class="store-name">
                    <i class="fas fa-${
                      store === "travel" ? "car" : "store"
                    } me-2"></i>
                    ${
                      store === "travel"
                        ? "Travel Costs"
                        : store.charAt(0).toUpperCase() + store.slice(1)
                    }
                </span>
                <span class="store-cost">$${cost.toFixed(2)}</span>
            </div>
        `
      )
      .join("");
  }

  async generateBill(format) {
    if (!this.currentRecipe) {
      this.showError("No recipe loaded");
      return;
    }

    try {
      this.showLoading(`Generating ${format.toUpperCase()} bill...`);

      const response = await fetch(`${this.apiBase}/generate-bill`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: `recipe_url=${encodeURIComponent(
          this.currentRecipe.url
        )}&format=${format}`,
      });

      const result = await response.json();

      if (!result.success) {
        throw new Error(result.error || "Failed to generate bill");
      }

      // Download the bill
      const downloadUrl = result.data.download_url;
      window.open(downloadUrl, "_blank");

      this.showSuccess(`${format.toUpperCase()} bill generated successfully!`);
      this.hideLoading();
    } catch (error) {
      console.error("Error generating bill:", error);
      this.showError(`Error generating bill: ${error.message}`);
      this.hideLoading();
    }
  }

  async downloadJSON() {
    if (!this.currentOptimization) {
      this.showError("No optimization data available");
      return;
    }

    const data = {
      recipe: this.currentRecipe,
      optimization: this.currentOptimization,
      generated_at: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });

    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `recipe_optimization_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    this.showSuccess("JSON data downloaded successfully!");
  }

  showLoading(text = "Loading...") {
    const loadingSection = document.getElementById("loadingSection");
    const loadingText = document.getElementById("loadingText");

    if (loadingText) {
      loadingText.textContent = text;
    }

    if (loadingSection) {
      loadingSection.style.display = "block";
    }
  }

  hideLoading() {
    const loadingSection = document.getElementById("loadingSection");
    if (loadingSection) {
      loadingSection.style.display = "none";
    }
  }

  showResults() {
    const resultsSection = document.getElementById("resultsSection");
    if (resultsSection) {
      resultsSection.style.display = "block";
    }
  }

  hideResults() {
    const resultsSection = document.getElementById("resultsSection");
    if (resultsSection) {
      resultsSection.style.display = "none";
    }
  }

  showError(message) {
    this.showAlert(message, "danger");
  }

  showSuccess(message) {
    this.showAlert(message, "success");
  }

  showAlert(message, type = "info") {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll(".alert-message");
    existingAlerts.forEach((alert) => alert.remove());

    // Create new alert
    const alertDiv = document.createElement("div");
    alertDiv.className = `alert alert-${type} alert-dismissible fade show alert-message`;
    alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

    // Insert after the main card
    const mainCard = document.querySelector(".card");
    if (mainCard) {
      mainCard.parentNode.insertBefore(alertDiv, mainCard.nextSibling);
    }

    // Auto-remove after 5 seconds
    setTimeout(() => {
      if (alertDiv.parentNode) {
        alertDiv.remove();
      }
    }, 5000);
  }
}

// Initialize app when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  window.app = new RecipeShoplistApp();
});

// Utility functions
function formatCurrency(amount) {
  return new Intl.NumberFormat("en-AU", {
    style: "currency",
    currency: "AUD",
  }).format(amount);
}

function formatTime(seconds) {
  if (seconds < 60) {
    return `${seconds.toFixed(1)}s`;
  } else {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
  }
}
