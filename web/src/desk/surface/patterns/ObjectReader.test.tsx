import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { ObjectReader, ReadingDocument } from "../../surface";
afterEach(cleanup);
it("starts with facts and keeps stored words in its reading well", () => {
  render(<ObjectReader label="Decision" facts={[{label:"State",value:"Decided"}]}><ReadingDocument>Keep the reason.</ReadingDocument></ObjectReader>);
  const reader = screen.getByText("State").closest(".surface-object-reader")!;
  expect(reader).toHaveAttribute("data-feedback-redact","true");
  expect(reader.firstElementChild).toHaveClass("surface-inspector-facts");
  expect(screen.getByText("Keep the reason.").closest(".surface-object-reading")).toBeTruthy();
});
it("shows an inline failure and retries in the same seat", () => {
  const retry = vi.fn();
  const {rerender}=render(<ObjectReader label="Result" failure="The engine did not answer" retry={{label:"Try again",run:retry}} />);
  expect(screen.getByRole("alert")).toHaveTextContent("The engine did not answer");
  fireEvent.click(screen.getByRole("button",{name:"Try again"}));expect(retry).toHaveBeenCalledOnce();
  rerender(<ObjectReader label="Result" running={{start:Date.now()}} lines={[{id:"read",text:"Read the saved reason"}]} />);
  expect(screen.queryByRole("alert")).toBeNull();
  expect(screen.getByRole("log")).toHaveTextContent("Read the saved reason");
  expect(screen.getByText("0:00")).toBeVisible();
});
