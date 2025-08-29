

// Tool search function
function searchTools() {
    const searchTerm = toolSearch.value.trim();
    
    if (!searchTerm) {
        alert('Please enter a search term');
        return;
    }

    // Fetch from the API
    fetch(`/find-tools?q=${encodeURIComponent(searchTerm)}`)
        .then(res => res.json())
        .then(data => {
            displayToolResults(data);
        })
        .catch(err => {
            console.error(err);
            alert('Error fetching tools');
        });
}

// Display tool search results
function displayToolResults(tools) {
    resultsContainer.innerHTML = '';

    if (tools.length === 0) {
        resultsContainer.innerHTML = '<p class="text-gray-500">No tools found matching your search.</p>';
        searchResults.classList.remove('hidden');
        return;
    }

    tools.forEach(tool => {
        const toolCard = document.createElement('div');
        toolCard.className = 'tool-card bg-white p-4 rounded-lg border border-gray-200 cursor-pointer hover:border-blue-300';
        toolCard.innerHTML = `
            <div class="flex items-center">
                <div class="w-12 h-12 bg-gray-200 rounded-lg mr-3 flex items-center justify-center">
                    <span class="text-gray-500 text-xs">Image</span>
                </div>
                <div>
                    <h4 class="font-medium">${tool.name}</h4>
                    <p class="text-sm text-gray-600">ID: ${tool.id}</p>
                    <p class="text-sm text-gray-600">Row: ${tool.loc_row}, Col: ${tool.loc_col}, Shelf: ${tool.loc_shelf}</p>
                    <p class="text-xs ${tool.status === 'Disponible' ? 'text-green-600' : 'text-red-600'}">${tool.status}</p>
                </div>
            </div>
        `;
        toolCard.addEventListener('click', () => selectTool(tool));
        resultsContainer.appendChild(toolCard);
    });

    searchResults.classList.remove('hidden');
}

function selectTool(tool) {
    selectedTool = tool;
    
    document.getElementById('selected-tool-name').textContent = tool.name;
    document.getElementById('selected-tool-id').textContent = `ID: ${tool.id}`;
    document.getElementById('selected-tool-location').textContent = `Row: ${tool.loc_row}, Col: ${tool.loc_col}, Shelf: ${tool.loc_shelf}`;
    
    selectedToolDiv.classList.remove('hidden');
    selectedToolDiv.scrollIntoView({ behavior: 'smooth' });
}

confirmToolBtn.addEventListener('click', () => {
    if (!selectedTool) {
        alert('Please select a tool first');
        return;
    }
    // Move to step 2 (Employee)
    goToStep(2);
});
