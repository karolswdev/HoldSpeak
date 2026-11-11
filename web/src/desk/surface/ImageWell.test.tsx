import {cleanup,fireEvent,render,screen} from "@testing-library/react";
import {afterEach,expect,it} from "vitest";
import {ImageWell} from "./ImageWell";
afterEach(cleanup);
it("names a failed image and tries a changed source",()=>{const {rerender}=render(<ImageWell src="blob:unreadable" alt="Step evidence"/>);fireEvent.error(screen.getByRole("img",{name:"Step evidence"}));expect(screen.getByRole("status").textContent).toBe("The image could not be read.");rerender(<ImageWell src="blob:readable" alt="Step evidence"/>);expect(screen.getByRole("img",{name:"Step evidence"})).toHaveAttribute("src","blob:readable");});
