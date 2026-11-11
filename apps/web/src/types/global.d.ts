// Global ambient declarations for CSS and static asset imports
declare module "*.css";
declare module "*.module.css" {
  const classes: { readonly [key: string]: string };
  export default classes;
}
