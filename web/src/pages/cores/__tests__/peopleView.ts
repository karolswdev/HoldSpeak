import { fireEvent, screen, waitFor, within } from "@testing-library/react";
export async function personView(label:string) {
  const button=await waitFor(()=>{
    const button=screen.getAllByRole("button",{name:"Person view"}).find(node=>node.closest(".object-list-toolbar"));
    if(!button)throw new Error("Person records are still loading");return button;
  });
  fireEvent.click(button);
  fireEvent.click(within(await screen.findByRole("menu",{name:"Person view"})).getByText(label,{exact:true}));
}
