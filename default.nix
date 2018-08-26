with import <nixpkgs> {}; {
  env = stdenv.mkDerivation {
    name = "flavk-env";
    buildInputs = [
      python3
      python3Packages.flask
    ];
  };
}
