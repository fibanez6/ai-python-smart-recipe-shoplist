// AI Recipe Shoplist Crawler - Frontend JavaScript

class RecipeShoplistApp {
  constructor() {
    this.apiBase = "/api/v1";
    this.currentRecipe = null;
    this.currentOptimization = null;
    this.currentShoppingItems = [];
    this.ingredientShoppingItemMap = new Map();
    this.demoManager = null;
    this.init();
  }

  init() {
    this.demoManager = new DemoManager(this);
    this.setupEventListeners();
    this.checkUrlParams();
  }

  setupEventListeners() {
    const form = document.getElementById("recipeForm");
    if (form) form.addEventListener("submit", (e) => this.handleRecipeSubmit(e));
    window.loadDemo = () => this.demoManager.loadDemo();
    this.setupStoreSelection();
  }

  setupStoreSelection() {
    const selectAllBtn = document.getElementById("selectAllStores");
    if (selectAllBtn) selectAllBtn.addEventListener("click", () => this.toggleSelectAllStores());
    document.querySelectorAll(".store-checkbox").forEach((cb) =>
      cb.addEventListener("change", () => this.updateSelectAllButton())
    );
  }

  toggleSelectAllStores() {
    const storeCheckboxes = Array.from(document.querySelectorAll(".store-checkbox")).filter(cb => !cb.disabled);
    const allSelected = storeCheckboxes.every(cb => cb.checked);
    storeCheckboxes.forEach(cb => cb.checked = !allSelected);
    this.updateSelectAllButton();
  }

  updateSelectAllButton() {
    const storeCheckboxes = Array.from(document.querySelectorAll(".store-checkbox"));
    const selectAllBtn = document.getElementById("selectAllStores");
    if (!selectAllBtn) return;
    const allSelected = storeCheckboxes.every(cb => cb.checked);
    const noneSelected = storeCheckboxes.every(cb => !cb.checked);
    if (allSelected) {
      selectAllBtn.innerHTML = '<i class="fas fa-times me-1"></i>Deselect All';
      selectAllBtn.className = "btn btn-sm btn-outline-danger";
    } else {
      selectAllBtn.innerHTML = '<i class="fas fa-check-double me-1"></i>Select All';
      selectAllBtn.className = "btn btn-sm btn-outline-primary";
    }
  }

  getSelectedStores() {
    return Array.from(document.querySelectorAll(".store-checkbox:checked")).map(cb => cb.value);
  }

  checkUrlParams() {
    const demoParam = new URLSearchParams(window.location.search).get("demo");
    if (demoParam === "true") this.demoManager.loadDemo();
  }

  async handleRecipeSubmit(event) {
    event.preventDefault();
    const url = new FormData(event.target).get("url");
    if (!url) return this.showError("Please enter a recipe URL");
    await this.processRecipe(url);
  }

  async processRecipe(url) {
    try {
      this.showLoading("Processing recipe...");
      this.hideResults();
      const recipeResponse = await fetch(`${this.apiBase}/process-recipe`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: `url=${encodeURIComponent(url)}`,
      });
      const recipeResult = await recipeResponse.json();
      if (!recipeResult.success) throw new Error(recipeResult.error || "Failed to process recipe");
      this.currentRecipe = recipeResult.data.recipe;
      if (!this.currentRecipe?.ingredients) throw new Error("Recipe data is invalid or missing ingredients");
      if (!Array.isArray(this.currentRecipe.ingredients)) this.currentRecipe.ingredients = [];
      const selectedStores = this.getSelectedStores();
      if (selectedStores.length === 0) throw new Error("Please select at least one grocery store");
      this.showLoading(`Finding shopping items in ${selectedStores.length} store(s)...`);
      const searchResponse = await fetch(`${this.apiBase}/search-stores`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ingredients: this.currentRecipe.ingredients, stores: selectedStores }),
      });
      const searchResult = await searchResponse.json();
      this.currentShoppingItems = searchResult.success ? searchResult.shopping_list_items || [] : [];
      this.mapShoppingItemsToIngredients();
      this.displayRecipeResults(recipeResult.data);
      this.hideLoading();
    } catch (error) {
      this.showError(`Error: ${error.message}`);
      this.hideLoading();
    }
  }

  mapShoppingItemsToIngredients() {
    this.ingredientShoppingItemMap.clear();
    this.currentShoppingItems.forEach(item => {
      const name = item?.ingredient?.name?.toLowerCase();
      if (name) {
        if (!this.ingredientShoppingItemMap.has(name)) this.ingredientShoppingItemMap.set(name, []);
        this.ingredientShoppingItemMap.get(name).push(item);
      }
    });
  }

  displayRecipeResults(data) {
    const resultsSection = document.getElementById("resultsSection");
    const resultsContent = document.getElementById("resultsContent");
    if (!resultsSection || !resultsContent) return;
    const recipe = data.recipe;
    resultsContent.innerHTML = `
      <div class="recipe-card fade-in">
        <div class="recipe-title"><i class="fas fa-utensils me-2"></i>${recipe.title}</div>
        <div class="recipe-meta">
          ${recipe.servings ? `<div class="meta-item"><i class="fas fa-users"></i> ${recipe.servings} servings</div>` : ""}
          ${recipe.prep_time ? `<div class="meta-item"><i class="fas fa-clock"></i> ${recipe.prep_time}</div>` : ""}
          ${recipe.cook_time ? `<div class="meta-item"><i class="fas fa-fire"></i> ${recipe.cook_time}</div>` : ""}
        </div>
        ${recipe.description ? `<p>${recipe.description}</p>` : ""}
        <a href="${recipe.url}" target="_blank" class="btn btn-outline-primary btn-sm">
          <i class="fas fa-external-link-alt me-1"></i>View Original Recipe
        </a>
      </div>
      <div class="mb-4">
        <h5 class="mb-3"><i class="fas fa-shopping-basket me-2"></i>Ingredients (${recipe.ingredients?.length || 0})</h5>
        <div class="ingredients-grid">${this.renderSimpleIngredients(recipe.ingredients || [])}</div>
      </div>
      ${recipe.instructions?.length ? `
        <div class="mb-4">
          <h5 class="mb-3"><i class="fas fa-list-ol me-2"></i>Instructions</h5>
          <ol class="list-group list-group-numbered">
            ${recipe.instructions.map(i => `<li class="list-group-item">${i}</li>`).join("")}
          </ol>
        </div>` : ""}
      <div class="alert alert-info">
        <h6><i class="fas fa-info-circle me-2"></i>Next Steps</h6>
        <p class="mb-2">Recipe processed successfully! You can now:</p>
        <ul class="mb-0">
          <li>Use the <a href="/api/v1/search-stores" target="_blank">Store Search API</a> to find shopping items</li>
          <li>Check the <a href="/api/v1/docs" target="_blank">API documentation</a> for more endpoints</li>
        </ul>
      </div>
    `;
    resultsSection.style.display = "block";
    resultsSection.scrollIntoView({ behavior: "smooth" });
  }

  renderSimpleIngredients(ingredients) {
    return ingredients
      .filter(i => i && typeof i === "object")
      .map(ingredient => {
        const name = ingredient.name || "Unknown Ingredient";
        const quantity = ingredient.quantity ? `${ingredient.quantity} ${ingredient.unit || ""}`.trim() : "As needed";
        const key = typeof ingredient.name === "string" ? ingredient.name.toLowerCase() : "";
        const shoppingArr = key ? this.ingredientShoppingItemMap.get(key) || [] : [];
        const bestProduct = shoppingArr[0]?.selected_product || null;
        let imageUrl = bestProduct?.image_url;
        if (!imageUrl) imageUrl = this.generatePlaceholderImage(name);
        let imageSection = `<div class="ingredient-image">
          <img src="${imageUrl}" alt="${name}" class="img-fluid rounded" style="width:80px;height:80px;object-fit:cover;"
            onerror="this.src='${this.generatePlaceholderImage(name)}';this.onerror=null;">
        </div>`;
        let productInfo = "";
        if (shoppingArr[0]?.store_options) {
          productInfo = `<div class="product-info">`;
          Object.entries(shoppingArr[0].store_options).forEach(([store, product]) => {
            const isSelected = bestProduct && product.url === bestProduct.url;
            productInfo += `
              <div class="store-product${isSelected ? " selected-product" : ""}">
                <small class="${isSelected ? "text-success fw-bold" : "text-secondary"}">
                  <i class="fas fa-store me-1"></i>${store} - $${(product.price || 0).toFixed(2)} ${product.price_unit || ""}
                </small><br>
                ${product.url
                  ? `<a href="${product.url}" target="_blank" class="text-decoration-none">
                      <small class="${isSelected ? "text-primary fw-bold" : "text-muted"}">
                        <i class="fas fa-external-link-alt me-1"></i>${product.name || "Product name unavailable"}
                      </small>
                    </a>`
                  : `<small class="text-muted">${product.name || "Product name unavailable"}</small>`
                }
              </div>`;
          });
          productInfo += `</div>`;
        } else if (bestProduct) {
          productInfo = `<div class="product-info">
            <small class="text-success"><i class="fas fa-store me-1"></i>${bestProduct.store || "Unknown Store"} - $${(bestProduct.price || 0).toFixed(2)} ${bestProduct.price_unit || ""}</small><br>
            ${bestProduct.url
              ? `<a href="${bestProduct.url}" target="_blank" class="text-decoration-none">
                  <small class="text-primary"><i class="fas fa-external-link-alt me-1"></i>${bestProduct.name || "Product name unavailable"}</small>
                </a>`
              : `<small class="text-muted">${bestProduct.name || "Product name unavailable"}</small>`
            }
          </div>`;
        } else {
          productInfo = `<div class="product-info"><small class="text-warning"><i class="fas fa-search me-1"></i>No shopping products found</small></div>`;
        }
        const totalCost = shoppingArr[0]?.total_cost ?? null;
        return `<div class="ingredient-item">
          ${imageSection}
          <div class="ingredient-details flex-grow-1">
            <h6>${name}</h6>
            <div class="ingredient-quantity">${quantity}</div>
            <small class="text-muted">${ingredient.original_text || ""}</small>
            ${productInfo}
          </div>
          <div class="text-end"><strong class="text-success">${totalCost !== null ? `$${totalCost.toFixed(2)}` : "-"}</strong></div>
        </div>`;
      }).join("");
  }

  generatePlaceholderImage(name) {
    const hash = this.simpleHash(name);
    const seed = hash % 1000;
    const keywords = ["food", "ingredient", "grocery", "fresh", "kitchen"];
    const keyword = keywords[hash % keywords.length];
    return `https://source.unsplash.com/200x200/?${keyword}&sig=${seed}`;
  }

  simpleHash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) hash = ((hash << 5) - hash + str.charCodeAt(i)) & hash;
    return Math.abs(hash);
  }

  displayResults(data) {
    const resultsSection = document.getElementById("resultsSection");
    const resultsContent = document.getElementById("resultsContent");
    if (!resultsSection || !resultsContent) return;
    const { recipe, optimization, summary } = data;
    resultsContent.innerHTML = `
      <div class="recipe-card fade-in">
        <div class="recipe-title"><i class="fas fa-utensils me-2"></i>${recipe.title}</div>
        <div class="recipe-meta">
          ${recipe.servings ? `<div class="meta-item"><i class="fas fa-users"></i> ${recipe.servings} servings</div>` : ""}
          ${recipe.prep_time ? `<div class="meta-item"><i class="fas fa-clock"></i> ${recipe.prep_time}</div>` : ""}
          ${recipe.cook_time ? `<div class="meta-item"><i class="fas fa-fire"></i> ${recipe.cook_time}</div>` : ""}
        </div>
        ${recipe.description ? `<p>${recipe.description}</p>` : ""}
      </div>
      <div class="optimization-summary fade-in">
        <h4 class="mb-3"><i class="fas fa-chart-line me-2"></i>Optimization Results</h4>
        <div class="summary-stats">
          <div class="stat-item"><span class="stat-value">$${summary.total_cost.toFixed(2)}</span><span class="stat-label">Total Cost</span></div>
          <div class="stat-item"><span class="stat-value">${summary.stores_count}</span><span class="stat-label">Stores</span></div>
          <div class="stat-item"><span class="stat-value">${summary.items_found}/${summary.items_total}</span><span class="stat-label">Items Found</span></div>
          <div class="stat-item"><span class="stat-value">$${summary.savings.toFixed(2)}</span><span class="stat-label">Savings</span></div>
        </div>
      </div>
      <div class="mb-4">
        <h5 class="mb-3"><i class="fas fa-shopping-basket me-2"></i>Shopping List</h5>
        <div class="ingredients-grid">${this.renderIngredients(optimization.items)}</div>
      </div>
      <div class="stores-breakdown">
        <h6 class="mb-3"><i class="fas fa-store me-2"></i>Store Breakdown</h6>
        ${this.renderStoreBreakdown(optimization.stores_breakdown)}
      </div>
      <div class="bill-actions">
        <button class="btn btn-success" onclick="app.generateBill('pdf')"><i class="fas fa-file-pdf me-1"></i>Generate PDF Bill</button>
        <button class="btn btn-outline-success" onclick="app.generateBill('html')"><i class="fas fa-file-code me-1"></i>Generate HTML Bill</button>
        <button class="btn btn-outline-primary" onclick="app.downloadJSON()"><i class="fas fa-download me-1"></i>Download JSON</button>
      </div>
    `;
    resultsSection.style.display = "block";
    resultsSection.scrollIntoView({ behavior: "smooth" });
  }

  renderIngredients(items) {
    return items.map(item => {
      const { ingredient, selected_product: product, total_cost } = item;
      const quantity = ingredient.quantity ? `${ingredient.quantity} ${ingredient.unit || ""}`.trim() : "As needed";
      if (product) {
        return `<div class="ingredient-item">
          <div class="ingredient-icon"><i class="fas fa-check"></i></div>
          <div class="ingredient-details flex-grow-1">
            <h6>${ingredient.name}</h6>
            <div class="ingredient-quantity">${quantity}</div>
            <small class="text-muted">
              ${product.store} - 
              ${product.url
                ? `<a href="${product.url}" target="_blank" class="text-decoration-none text-primary">
                    <i class="fas fa-external-link-alt me-1"></i>${product.title || product.name}
                  </a>`
                : product.title || product.name
              } - $${product.price.toFixed(2)}
            </small>
          </div>
          <div class="text-end"><strong class="text-success">$${(total_cost || 0).toFixed(2)}</strong></div>
        </div>`;
      } else {
        return `<div class="ingredient-item">
          <div class="ingredient-icon bg-warning"><i class="fas fa-exclamation"></i></div>
          <div class="ingredient-details flex-grow-1">
            <h6>${ingredient.name}</h6>
            <div class="ingredient-quantity">${quantity}</div>
            <small class="text-danger">Not found in stores</small>
          </div>
          <div class="text-end"><span class="text-muted">-</span></div>
        </div>`;
      }
    }).join("");
  }

  renderStoreBreakdown(breakdown) {
    return Object.entries(breakdown).map(([store, cost]) => `
      <div class="store-item">
        <span class="store-name"><i class="fas fa-${store === "travel" ? "car" : "store"} me-2"></i>
          ${store === "travel" ? "Travel Costs" : store.charAt(0).toUpperCase() + store.slice(1)}
        </span>
        <span class="store-cost">$${cost.toFixed(2)}</span>
      </div>
    `).join("");
  }

  async generateBill(format) {
    if (!this.currentRecipe) return this.showError("No recipe loaded");
    try {
      this.showLoading(`Generating ${format.toUpperCase()} bill...`);
      const response = await fetch(`${this.apiBase}/generate-bill`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: `recipe_url=${encodeURIComponent(this.currentRecipe.url)}&format=${format}`,
      });
      const result = await response.json();
      if (!result.success) throw new Error(result.error || "Failed to generate bill");
      window.open(result.data.download_url, "_blank");
      this.showSuccess(`${format.toUpperCase()} bill generated successfully!`);
      this.hideLoading();
    } catch (error) {
      this.showError(`Error generating bill: ${error.message}`);
      this.hideLoading();
    }
  }

  async downloadJSON() {
    if (!this.currentOptimization) return this.showError("No optimization data available");
    const data = {
      recipe: this.currentRecipe,
      optimization: this.currentOptimization,
      generated_at: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
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
    if (loadingText) loadingText.textContent = text;
    if (loadingSection) loadingSection.style.display = "block";
  }

  hideLoading() {
    const loadingSection = document.getElementById("loadingSection");
    if (loadingSection) loadingSection.style.display = "none";
  }

  showResults() {
    const resultsSection = document.getElementById("resultsSection");
    if (resultsSection) resultsSection.style.display = "block";
  }

  hideResults() {
    const resultsSection = document.getElementById("resultsSection");
    if (resultsSection) resultsSection.style.display = "none";
  }

  showError(message) { this.showAlert(message, "danger"); }
  showSuccess(message) { this.showAlert(message, "success"); }

  showAlert(message, type = "info") {
    document.querySelectorAll(".alert-message").forEach(alert => alert.remove());
    const alertDiv = document.createElement("div");
    alertDiv.className = `alert alert-${type} alert-dismissible fade show alert-message`;
    alertDiv.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
    const mainCard = document.querySelector(".card");
    if (mainCard) mainCard.parentNode.insertBefore(alertDiv, mainCard.nextSibling);
    setTimeout(() => alertDiv.parentNode && alertDiv.remove(), 5000);
  }
}

document.addEventListener("DOMContentLoaded", () => { window.app = new RecipeShoplistApp(); });

function formatCurrency(amount) {
  return new Intl.NumberFormat("en-AU", { style: "currency", currency: "AUD" }).format(amount);
}

function formatTime(seconds) {
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
}
