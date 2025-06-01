{ pkgs ? import <nixpkgs> {} }:
  pkgs.mkShell {
    nativeBuildInputs = with pkgs; [
      playwright-driver.browsers
    ];

    packages = [
      (pkgs.python312.withPackages (python-pkgs: with python-pkgs; [
        # LangChain ecosystem
        langchain
        langchain-openai
        langchain-community
        numpy
        
        # Web automation and scraping
        playwright
        beautifulsoup4
        lxml
        
        # OpenAI API client
        openai
        
        # Web framework
        flask
        
        # Data validation and settings
        pydantic
        
        # Utilities
        python-dotenv
        nest-asyncio
        aiohttp
      ]))
    ];

    shellHook = ''
      export PLAYWRIGHT_BROWSERS_PATH=${pkgs.playwright-driver.browsers}
      export PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=true
      zsh
    '';
}